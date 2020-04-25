# Copyright (C) 2019-2020, TomTom (http://tomtom.com).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API reference storage and search."""

import re

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from .model import Member, ReferableElement


class AmbiguousLookupError(Exception):
    """There are multiple elements matching your query. Make the query more specific.

    Attributes:
        candidates: All candidates that match the search query.
    """
    candidates: List[ReferableElement]

    def __init__(self, candidates: List[ReferableElement]):
        self.candidates = candidates


class ElementFilter(ABC):
    """Base class for filters that can be applied to find specific elements in the API reference.
    """
    @abstractmethod
    def __call__(self, potential_match: ReferableElement) -> bool:
        """Apply the filter to a potential match.

        Args:
            potential_match: Element to match the filter to.

        Returns:
            True if the element matches the filer, False if not.
        """
        return False

    @property
    @abstractmethod
    def applies(self) -> bool:
        """Does this filter currently apply?

        If a filter does not apply, it should be excluded when filtering elements.

        Returns:
            True if the filter applies.
        """
        return False


class CombinedFilter(ElementFilter):
    """Combination of filters that acts as a single filter.

    All contained filters must match for this filter to match.
    """
    _filters: List[ElementFilter]

    def __init__(self, *filters: ElementFilter):
        """Construct a combined filter.

        Args:
            filters: All filters that need to be combined.
        """
        self._filters = [f for f in filters if f.applies]

    def __call__(self, potential_match: ReferableElement) -> bool:
        return all(f(potential_match) for f in self._filters)

    @property
    def applies(self) -> bool:
        return len(self._filters) > 0

    def add(self, filter_: ElementFilter):
        """Add a filter to the combined filter."""
        if filter_.applies:
            self._filters.append(filter_)


class SimpleAttributeFilter(ElementFilter):
    """Filter that checks the content of a specific attribute on the potential match.

    The filter matches if the attribute exists and matches. It will check that the attribute exists
    before matching.

    Attributes:
        ATTR_NAME: Name of the attribute to match.
    """
    ATTR_NAME: str
    _value: Optional[str]

    def __init__(self, value: Optional[str]):
        """Construct the filter.

        Args:
            value: The value the attribute should match, or None to disable the filter.
        """
        self._value = value

    def __call__(self, potential_match: ReferableElement) -> bool:
        return getattr(potential_match, self.ATTR_NAME, None) == self._value

    @property
    def applies(self) -> bool:
        return self._value is not None


class IdFilter(SimpleAttributeFilter):
    """Filter on the unique id."""
    ATTR_NAME = "id"


class NamespaceList(list):
    def startswith(self, other: list) -> bool:
        if len(self) < len(other):
            return False
        return self[:len(other)] == other

    def endswith(self, other: list) -> bool:
        if len(self) < len(other):
            return False
        return self[-len(other):] == other


class NameFilter(ElementFilter):
    """Filter on the name of the element.

    Optionally takes a namespace to start searching from.
    """
    _name: Optional[str] = None
    _namespace: Optional[str] = None

    _name_parts: NamespaceList
    _namespace_parts: NamespaceList

    NAMESPACE_SEPARATORS = "::", "."

    def __init__(self, name: Optional[str], namespace: Optional[str] = None):
        self._name = name
        self._namespace = namespace

        if name is not None and namespace is not None:
            self._name_parts = self._split_namespaces(name)
            self._namespace_parts = self._split_namespaces(namespace)
        else:
            self._name_parts = NamespaceList()
            self._namespace_parts = NamespaceList()

    def __call__(self, potential_match: ReferableElement) -> bool:
        if self._name is None:
            return False

        full_name = getattr(potential_match, "full_name", None)
        if full_name is None:
            return False

        if self._namespace is None:
            return self._full_name_match(full_name)
        else:
            return self._namespaced_match(full_name)

    @property
    def applies(self) -> bool:
        return self._name is not None

    def _full_name_match(self, full_name: str) -> bool:
        return full_name == self._name

    def _namespaced_match(self, full_name: str) -> bool:
        if self._name is None:
            return False

        if not full_name.endswith(self._name):
            return False

        full_name_parts = self._split_namespaces(full_name)

        if not full_name_parts.endswith(self._name_parts):
            return False

        del full_name_parts[-len(self._name_parts):]
        if len(full_name_parts) == 0:
            return True

        return self._namespace_parts.startswith(full_name_parts)

    @classmethod
    def _split_namespaces(cls, name: str) -> NamespaceList:
        for sep in cls.NAMESPACE_SEPARATORS:
            if sep in name:
                namespaces = name.split(sep)
                break
        else:
            return NamespaceList([name])

        return NamespaceList(ns.strip() for ns in namespaces if not ns.isspace() and ns != "")


class KindFilter(SimpleAttributeFilter):
    """Filter on the kind of element."""
    ATTR_NAME = "kind"


class LangFilter(SimpleAttributeFilter):
    """Filter on the programming language of the element."""
    ATTR_NAME = "language"


class ParameterTypeMatcher(ElementFilter):
    """Filter elements based on the parameter types they accept.

    Used to disambiguate callable elements, and any other type that has typed parameters.

    It takes a specification of the format:
      <NAME>(<ARG TYPE 1>[, <ARG_TYPE 2>[, ...]])

    The name will be separated from the parameter type list, so it can be used for initial filtering
    on name.

    Attributes:
        name:      Base name of the element.
        arg_types: List of types the parameters should accept.
    """
    name: str
    arg_types: Optional[List[str]]

    def __init__(self, function_spec: Optional[str]):
        """Construct a parameter type filter.

        Args:
            function_spec: Specification of the element name and the required parameter types.
        """
        if function_spec is not None:
            self._parse_function_spec(function_spec)
        else:
            self.name = ""
            self.arg_types = None

    def __call__(self, potential_match: ReferableElement) -> bool:
        if self.arg_types is None:
            return True

        if not isinstance(potential_match, Member):
            return False

        params = potential_match.params or []

        if not self.arg_types and not params:
            return True

        if len(self.arg_types) != len(params):
            return False

        for expected_type, param in zip(self.arg_types, params):
            assert param.type

            if self._normalize(str(param.type)) != expected_type:
                return False

        return True

    @property
    def applies(self) -> bool:
        return self.arg_types is not None

    def _parse_function_spec(self, function_spec: str) -> None:
        name, args_spec = self._split_name_and_args(function_spec)
        self.name = self._normalize(name)
        self.arg_types = self._split_args(args_spec)

    @staticmethod
    def _split_name_and_args(function_spec: str) -> Tuple[str, Optional[str]]:
        ARGS_START = "("
        ARGS_END = ")"

        args_start_index = function_spec.find(ARGS_START)
        args_end_index = function_spec.rfind(ARGS_END)

        if args_start_index == -1 or args_end_index == -1 or args_start_index > args_end_index:
            # No valid argument specification found, use full name match
            return function_spec, None

        return (function_spec[0:args_start_index],
                function_spec[args_start_index + 1:args_end_index])

    @classmethod
    def _split_args(cls, args_spec: Optional[str]) -> Optional[List[str]]:
        ARGS_SEP = ","
        NESTED_START = "({[<"
        NESTED_END = ")}]>"

        if args_spec is None:
            return None

        if len(args_spec) == 0 or args_spec.isspace():
            return []

        if ARGS_SEP not in args_spec:
            return [cls._normalize(args_spec)]

        cursor = 0
        nested = 0
        args = []
        while cursor < len(args_spec):
            if args_spec[cursor] in NESTED_START:
                nested += 1
            elif args_spec[cursor] in NESTED_END:
                nested -= 1
            elif args_spec[cursor] == ARGS_SEP and nested == 0:
                args.append(cls._normalize(args_spec[0:cursor]))
                args_spec = args_spec[cursor + 1:]
                cursor = 0
                continue

            cursor += 1

        if args_spec and not args_spec.isspace():
            args.append(cls._normalize(args_spec))

        return args

    @staticmethod
    def _normalize(name: str) -> str:
        name = name.strip()
        name = re.sub(r"\s+", " ", name)
        name = re.sub(r"(\w)\s(\W)", r"\1\2", name)
        name = re.sub(r"(\W)\s(\w)", r"\1\2", name)
        name = re.sub(r"(\W)\s(\W)", r"\1\2", name)
        return name


class ApiReference:
    """Collection of API reference information.

    Mainains the collection of available elements and allows searching for specific elements.

    Attributes:
        elements: All contained API reference elements.
    """
    elements: List[ReferableElement]

    def __init__(self):
        self.elements = []

    def find(self,
             name: Optional[str] = None,
             *,
             namespace: Optional[str] = None,
             kind: Optional[str] = None,
             lang: Optional[str] = None,
             target_id: Optional[str] = None) -> Optional[ReferableElement]:
        """Find information about an API element.

        The minimum search uses either `name` or `target_id`. If `target_id` is not None, all other
        arguments are ignored.

        For `name` you can specify the types of function arguments to disambiguate between
        overloads. If function arguments are supplied, a result is only returned if the argument
        types match exactly. Function argument types must be given between parentheses, where
        multiple types are separated by a comma.

        Args:
            name:      Name of the object.
            namespace: [Optional] Namespace to start searching in.
            kind:      [Optional] Kind of object.
            lang:      [Optional] Programming language.
            target_id: [Optional] Id of referred object

        Returns:
            Information about the API element, or None if not found.

        Raises:
            AmbiguousLookupError: There are multiple matching elements. Make your query more narrow.
        """
        if target_id is not None:
            return self._find(IdFilter(target_id))

        paramtype_matcher = ParameterTypeMatcher(name)
        if paramtype_matcher.applies:
            name = paramtype_matcher.name

        previous_error = None
        if namespace is not None:
            try:
                element = self._find(
                    CombinedFilter(NameFilter(name, namespace), KindFilter(kind), LangFilter(lang),
                                   paramtype_matcher))
                if element is not None:
                    return element
            except AmbiguousLookupError as e:
                previous_error = e

        element = self._find(
            CombinedFilter(NameFilter(name), KindFilter(kind), LangFilter(lang), paramtype_matcher))
        if element is None and previous_error is not None:
            raise previous_error
        return element

    def _find(self, element_filter: ElementFilter):
        matches = [e for e in self.elements if element_filter(e)]

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            raise AmbiguousLookupError(matches)
        else:
            return None
