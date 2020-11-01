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
"""
Tests for Objective C template helpers.
"""

import pytest

from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Member, ReturnValue, Parameter, TypeRef
from asciidoxy.templates.objc.helpers import ObjcTemplateHelper

from .builders import SimpleClassBuilder


@pytest.fixture
def objc_class():
    builder = SimpleClassBuilder("objc")
    builder.name("MyClass")

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("enum", "class", "protocol", "trash"):
            builder.simple_member(kind=member_type, prot=visibility)

        # add property
        builder.member_property(prot=visibility)
        # add some method
        builder.member_function(prot=visibility, name=visibility.capitalize() + "Method")
        # add static method
        builder.member_function(prot=visibility,
                                name=visibility.capitalize() + "StaticMethod",
                                static=True)

    # forbidden method
    builder.member_function(name="NS_UNAVAILABLE", prot="public")

    return builder.compound


@pytest.fixture
def helper(generating_api, objc_class):
    return ObjcTemplateHelper(generating_api, objc_class, InsertionFilter())


def test_public_methods__no_filter(helper):
    result = [m.name for m in helper.public_methods()]
    assert sorted(result) == sorted(["NS_UNAVAILABLE", "PublicMethod"])


def test_public_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="-NS_")
    result = [m.name for m in helper.public_methods()]
    assert sorted(result) == sorted(["PublicMethod"])


def test_public_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_methods()]
    assert len(result) == 0


def test_public_class_methods__no_filter(helper):
    result = [m.name for m in helper.public_class_methods()]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_class_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.public_class_methods()]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_class_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_class_methods()]
    assert len(result) == 0


def test_public_properties__no_filter(helper):
    result = [m.name for m in helper.public_properties()]
    assert result == ["PublicProperty"]


def test_public_properties__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.public_properties()]
    assert result == ["PublicProperty"]


def test_public_properties__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_properties()]
    assert len(result) == 0


def test_public_simple_enclosed_types__no_filter(helper):
    result = [m.name for m in helper.public_simple_enclosed_types()]
    assert sorted(result) == sorted([
        "PublicEnum", "ProtectedEnum", "PrivateEnum", "PublicClass", "ProtectedClass",
        "PrivateClass", "PublicProtocol", "ProtectedProtocol", "PrivateProtocol"
    ])


def test_public_simple_enclosed_types__filter_match(helper):
    helper.insert_filter = InsertionFilter(members=".*Enum")
    result = [m.name for m in helper.public_simple_enclosed_types()]
    assert sorted(result) == sorted([
        "PublicEnum",
        "ProtectedEnum",
        "PrivateEnum",
    ])


def test_public_simple_enclosed_types__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_simple_enclosed_types()]
    assert len(result) == 0


def test_objc_method_signature__no_params_simple_return(generating_api):
    method = Member("objc")
    method.name = "start"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="void")
    helper = ObjcTemplateHelper(generating_api)
    assert helper.method_signature(method) == "- (void)start"


def test_objc_method_signature__no_params_link_return(generating_api):
    method = Member("objc")
    method.name = "retrieveValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")
    method.returns.type.id = "objc-value"
    helper = ObjcTemplateHelper(generating_api)
    assert helper.method_signature(method) == "- (xref:objc-value[Value])retrieveValue"


def test_objc_method_signature__one_param(generating_api):
    method = Member("objc")
    method.name = "setValue:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")
    method.returns.type.id = "objc-value"

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")
    method.params = [param1]

    helper = ObjcTemplateHelper(generating_api)
    assert helper.method_signature(method) == "- (xref:objc-value[Value])setValue:(Type1)arg1"


def test_objc_method_signature__multiple_params_simple_return(generating_api):
    method = Member("objc")
    method.name = "setValue:withUnit:andALongerParam:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")

    param2 = Parameter()
    param2.name = "arg2"
    param2.type = TypeRef("objc", "Type2")
    param2.type.id = "objc-type2"

    param3 = Parameter()
    param3.name = "arg3"
    param3.type = TypeRef("objc", "Type3")

    method.params = [param1, param2, param3]

    helper = ObjcTemplateHelper(generating_api)
    assert (helper.method_signature(method) == """\
- (Value)setValue:(Type1)arg1
         withUnit:(xref:objc-type2[Type2])arg2
  andALongerParam:(Type3)arg3""")


def test_objc_method_signature__multiple_params_linked_return(generating_api):
    method = Member("objc")
    method.name = "setValue:withUnit:andALongerParam:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")
    method.returns.type.id = "objc-value"

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")

    param2 = Parameter()
    param2.name = "arg2"
    param2.type = TypeRef("objc", "Type2")
    param2.type.id = "objc-type2"

    param3 = Parameter()
    param3.name = "arg3"
    param3.type = TypeRef("objc", "Type3")

    method.params = [param1, param2, param3]

    helper = ObjcTemplateHelper(generating_api)
    assert (helper.method_signature(method) == """\
- (xref:objc-value[Value])setValue:(Type1)arg1
         withUnit:(xref:objc-type2[Type2])arg2
  andALongerParam:(Type3)arg3""")


def test_objc_method_signature__class_method(generating_api):
    method = Member("objc")
    method.name = "start"
    method.static = True
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="void")
    helper = ObjcTemplateHelper(generating_api)
    assert helper.method_signature(method) == "+ (void)start"
