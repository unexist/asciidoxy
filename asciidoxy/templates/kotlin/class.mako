## Copyright (C) 2019-2020, TomTom (http://tomtom.com).
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

################################################################################ Helper includes ##
<%!
from asciidoxy.templates.helpers import has
from asciidoxy.templates.java.helpers import JavaTemplateHelper
from asciidoxy.templates.kotlin.helpers import KotlinTemplateHelper
%>
<%
helper = KotlinTemplateHelper(api, element, insert_filter)
java_helper = JavaTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.name}]]${element.name}
${api.inserted(element)}

[source,kotlin,subs="-specialchars,macros+"]
----
class ${element.full_name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===

###################################################################################################
% if has(helper.public_complex_enclosed_types()):
|*Enclosed types*
|
% for enclosed in helper.public_complex_enclosed_types():
`xref:${enclosed.id}[${enclosed.name}]`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_constants()):
|*Constants*
|
% for constant in helper.public_constants():
`const val xref:${constant.id}[${constant.name}: ${constant.returns.type.name}]`::
${constant.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_constructors()):
|*Constructors*
|
% for constructor in helper.public_constructors():
`xref:${constructor.id}[${constructor.name}${helper.type_list(constructor.params)}]`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_properties()):
|*Properties*
|
% for prop in helper.public_properties():
`xref:${prop.id}[${prop.name}]`::
${prop.brief}
% endfor

% endif
###################################################################################################
% if has(java_helper.public_static_methods()):
|*Static Java methods*
|
% for method in java_helper.public_static_methods():
`xref:${method.id}[static ${java_helper.print_ref(method.returns.type, link=False)} ${method.name}${java_helper.type_list(method.params)}]`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_methods()):
|*Methods*
|
% for method in helper.public_methods():
% if method.returns and method.returns.type.name != 'void':
`xref:${method.id}[${method.name}${helper.type_list(method.params)}: ${helper.print_ref(method.returns.type, link=False)}]`::
% else:
`xref:${method.id}[${method.name}${helper.type_list(method.params)}]`::
% endif
${method.brief}
% endfor

% endif
|===

== Members
###################################################################################### Constants ##
% for constant in helper.public_constants():
[[${constant.id},${constant.name}]]
${api.inserted(constant)}
[source,kotlin,subs="-specialchars,macros+"]
----
const val ${constant.name}: ${constant.returns.type.name}
----

${constant.brief}

${constant.description}

'''
% endfor
################################################################################### Constructors ##
% for constructor in helper.public_constructors():
[[${constructor.id},${constructor.name}]]
${api.inserted(constructor)}
[source,kotlin,subs="-specialchars,macros+"]
----
${helper.method_signature(constructor)}
----

${constructor.brief}

${constructor.description}

% if constructor.params or constructor.exceptions:
[cols='h,5a']
|===
% if constructor.params:
| Parameters
|
% for param in constructor.params:
`${helper.print_ref(param.type)} ${param.name}`::
${param.description}

% endfor
% endif
% if constructor.exceptions:
| Throws
|
% for exception in constructor.exceptions:
`${helper.print_ref(exception.type)}`::
${exception.description}

% endfor
%endif
|===
% endif
'''
% endfor
##################################################################################### Properties ##
% for prop in helper.public_properties():
[[${prop.id},${prop.name}]]
${api.inserted(prop)}
[source,kotlin,subs="-specialchars,macros+"]
----
val ${prop.name}: ${prop.returns.type.name}
----

${prop.brief}

${prop.description}

'''
% endfor
################################################################################# Static methods ##
% for method in java_helper.public_static_methods():
[[${method.id},${method.name}]]
${api.inserted(method)}
[source,java,subs="-specialchars,macros+"]
----
${java_helper.method_signature(method)}
----

${method.brief}

${method.description}

% if method.params or method.exceptions or method.returns:
[cols='h,5a']
|===
% if method.params:
| Parameters
|
% for param in method.params:
`${java_helper.print_ref(param.type)} ${param.name}`::
${param.description}

% endfor
% endif
% if method.returns and method.returns.type.name != "void":
| Returns
|
`${java_helper.print_ref(method.returns.type)}`::
${method.returns.description}

% endif
% if method.exceptions:
| Throws
|
% for exception in method.exceptions:
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif
'''
% endfor
######################################################################################## Methods ##
% for method in helper.public_methods():
[[${method.id},${method.name}]]
${api.inserted(method)}
[source,kotlin,subs="-specialchars,macros+"]
----
${helper.method_signature(method)}
----

${method.brief}

${method.description}

% if method.params or method.exceptions or method.returns:
[cols='h,5a']
|===
% if method.params:
| Parameters
|
% for param in method.params:
`${param.name}: ${helper.print_ref(param.type)}`::
${param.description}

% endfor
% endif
% if method.returns and method.returns.type.name != "void":
| Returns
|
`${helper.print_ref(method.returns.type)}`::
${method.returns.description}

% endif
% if method.exceptions:
| Throws
|
% for exception in method.exceptions:
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif
'''
% endfor

############################################################################# Inner/Nested types ##

% for enclosed in helper.public_complex_enclosed_types():
${api.insert_fragment(enclosed, insert_filter)}
% endfor
