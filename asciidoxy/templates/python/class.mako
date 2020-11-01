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
from asciidoxy.templates.python.helpers import PythonTemplateHelper
%>
<%
helper = PythonTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.full_name}]]${element.name}
${api.inserted(element)}

[source,python,subs="-specialchars,macros+"]
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
`xref:${enclosed.id}[+++${enclosed.name}+++]`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_constructors()):
|*Constructors*
|
% for constructor in helper.public_constructors():
`xref:${constructor.id}[+++${constructor.name}+++]`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_variables()):
|*Variables*
|
% for variable in helper.public_variables():
`xref:${variable.id}[+++${variable.name}+++]`::
${variable.brief}
% endfor
% endif
###################################################################################################
% if has(helper.public_static_methods()):
|*Static methods*
|
% for method in helper.public_static_methods():
`xref:${method.id}[+++${method.name}+++]`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(helper.public_methods()):
|*Methods*
|
% for method in helper.public_methods():
`xref:${method.id}[+++${method.name}+++]`::
${method.brief}
% endfor

% endif
|===

== Members

################################################################################### Constructors ##
% for constructor in helper.public_constructors():
${api.insert_fragment(constructor, insert_filter)}
'''
% endfor
###################################################################################### Variables ##
% for variable in helper.public_variables():
[[${variable.id},${variable.name}]]
${api.inserted(variable)}

[source,python,subs="-specialchars,macros+"]
----
% if variable.returns is not None:
${variable.name}: ${helper.print_ref(variable.returns.type)}
% else:
${variable.name}
% endif
----

${variable.brief}

${variable.description}

'''
% endfor
################################################################################# Static methods ##
% for method in helper.public_static_methods():
${api.insert_fragment(method, insert_filter)}
'''
% endfor
######################################################################################## Methods ##
% for method in helper.public_methods():
${api.insert_fragment(method, insert_filter)}
'''
% endfor

############################################################################# Inner/Nested types ##

% for enclosed in helper.public_complex_enclosed_types():
${api.insert_fragment(enclosed, insert_filter)}
% endfor

