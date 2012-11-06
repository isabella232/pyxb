# -*- coding: utf-8 -*-
# Copyright 2009-2012, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Extensions of standard exceptions for PyXB events.

Yeah, I'd love this module to be named exceptions.py, but it can't
because the standard library has one of those, and we need to
reference it below.
"""

import exceptions

class PyXBException (exceptions.Exception):
    """Base class for exceptions that indicate a problem that the user should fix."""

    """The arguments passed to the exception constructor."""
    _args = None

    """The keywords passed to the exception constructor.

    @note: Do not pop values from the keywords array in subclass
    constructors that recognize and extract values from them.  They
    should be kept around so they're accessible generically."""
    _kw = None

    def __init__ (self, *args, **kw):
        """Create an exception indicating a PyXB-related problem.

        If no args are present, a default argument is taken from the
        C{message} keyword.

        @keyword message : Text to provide the user with information about the problem.
        """
        if 0 == len(args) and 'message' in kw:
            args = (kw.pop('message'),)
        self._args = args
        self._kw = kw
        exceptions.Exception.__init__(self, *args)

class SchemaValidationError (PyXBException):
    """Raised when the XML hierarchy does not appear to be valid for an XML schema."""
    pass

class NamespaceError (PyXBException):
    """Violation of some rule relevant to XML Namespaces"""
    def __init__ (self, namespace, *args, **kw):
        PyXBException.__init__(self, *args, **kw)
        self.__namespace = namespace

    def namespace (self): return self.__namespace

class NamespaceArchiveError (PyXBException):
    """Problem related to namespace archives"""
    pass

class SchemaUniquenessError (PyXBException):
    """Raised when somebody tries to create a schema component using a
    schema that has already been used in that namespace.  Import and
    include processing would have avoided this, so somebody asked for
    it specifically."""
    def __init__ (self, namespace, schema_location, existing_schema, *args, **kw):
        # Prior to 2.5, exceptions did not inherit from object, and
        # super could not be used.
        #super(SchemaUniquenessError, self).__init__(*args, **kw)
        PyXBException.__init__(self, *args, **kw)
        self.__namespace = namespace
        self.__schemaLocation = schema_location
        self.__existingSchema = existing_schema

    def namespace (self): return self.__namespace
    def schemaLocation (self): return self.__schemaLocation
    def existingSchema (self): return self.__existingSchema

class BindingGenerationError (PyXBException):
    """Raised when something goes wrong generating the binding classes"""
    pass

class NamespaceUniquenessError (NamespaceError):
    """Raised when an attempt is made to record multiple objects of the same name in the same namespace category."""
    pass

class NotInNamespaceError (PyXBException):
    '''Raised when a name is referenced that is not defined in the appropriate namespace.'''
    __namespace = None
    __ncName = None

class BadDocumentError (PyXBException):
    """Raised when processing document content and an error is encountered."""
    pass

class StructuralBadDocumentError (BadDocumentError):
    """Raised when processing document and the content model is not satisfied."""
    @property
    def element_use (self):
        """The L{pyxb.binding.content.ElementDeclaration} instance to which the content should conform, if available."""
        return self.__elementUse

    @property
    def container (self):
        """The L{pyxb.binding.basis.complexTypeDefinition} instance to which the content would belong, if available."""
        return self.__container

    @property
    def content (self):
        """The value which could not be reconciled with the content model."""
        return self.__content
    
    def __init__ (self, *args, **kw):
        """Raised when processing document and the content model is not satisfied.

        @keyword content : The value that could not be reconciled with the content model
        @keyword container : Optional binding instance into which the content was to be assigned
        @keyword element_use : Optional reference to an element use identifying the element to which the value was to be reconciled
        """
        self.__content = kw.pop('content', None)
        if args:
            self.__content = args[0]
        self.__container = kw.pop('container', None)
        self.__elementUse = kw.pop('element_use', None)
        if self.__content is not None:
            if self.__container is not None:
                kw.setdefault('message', '%s cannot accept wildcard content %s' % (self.__container, self.__content))
            elif self.__elementUse is not None:
                kw.setdefault('message', '%s not consistent with content model for %s' % (self.__content, self.__elementUse))
            else:
                kw.setdefault('message', str(self.__content))
        BadDocumentError.__init__(self, **kw)

class UnrecognizedDOMRootNodeError (StructuralBadDocumentError):
    """A root DOM node could not be resolved to a schema element"""

    node = None
    """The L{xml.dom.Element} instance that could not be recognized"""

    def __get_node_name (self):
        """The QName of the L{node} as a L{pyxb.namespace.ExpandedName}"""
        import pyxb.namespace
        return  pyxb.namespace.ExpandedName(self.node.namespaceURI, self.node.localName)
    node_name = property(__get_node_name)

    def __init__ (self, node):
        """@param node: the value for the L{node} attribute."""
        self.node = node
        super(UnrecognizedDOMRootNodeError, self).__init__(node)

class ValidationError (PyXBException):
    """Raised when something in the infoset fails to satisfy a content model or attribute requirement.

    All validation errors include a L{location} attribute which shows
    where in the original XML the problem occurred.  The attribute may
    be C{None} if the content did not come from an XML document, or
    the underlying XML infrastructure did not provide a location.

    More refined validation error exception classes add more attributes."""

    location = None
    """Where the error occurred in the document being parsed, if available."""

    def details (self):
        """Provide information describing why validation failed.

        In many cases, this is simple the informal string content that
        would be obtained through the C{str} built-in function.  For
        certain errors this method gives more details on what would be
        acceptable and where the descriptions can be found in the
        original schema.

        @return: a string description of validation failure"""
        return str(self)

class ElementValidationError (ValidationError):
    """Raised when a validation requirement for an element is not satisfied."""
    pass

class AbstractElementError (ElementValidationError):
    """Attempt to create an instance of an abstract element.

    Raised when an element is created and the identified binding is
    abstract.  Such elements cannot be created directly; instead the
    creation must derive from an instance of the abstract element's
    substitution group.

    Since members of the substitution group self-identify using the
    C{substitutionGroup} attribute, there is no general way to find
    the set of elements which would be acceptable in place of the
    abstract element."""

    element = None
    """The abstract L{pyxb.binding.basis.element} in question"""

    value = None
    """The value proposed for the L{element}.  This is usually going
    to be a C{xml.dom.Node} used in the attempt to create the element,
    C{None} if the abstract element was invoked without a node, or
    another type if
    L{pyxb.binding.content.ElementDeclaration.toDOM} is
    mis-used."""

    def __init__ (self, element, location, value=None):
        """@param element: the value for the L{element} attribute.
        @param location: the value for the L{location} attribute.
        @param value: the value for the L{value} attribute."""
        self.element = element
        self.location = location
        self.value = value
        super(AbstractElementError, self).__init__(element, location, value)

    def __str__ (self):
        return 'Cannot instantiate abstract element %s directly' % (self.element.name(),)

class ComplexTypeValidationError (ValidationError):
    """Raised when a validation requirement for a complex type is not satisfied."""
    pass

class AbstractInstantiationError (ComplexTypeValidationError):
    """Attempt to create an instance of an abstract complex type.

    These types are analogous to abstract base classes, and cannot be
    created directly.  A type should be used that extends the abstract
    class.

    When an incoming document is missing the xsi:type attribute which
    redirects an element with an abstract type to the correct type,
    the L{node} attribute is provided so the user can get a clue as to
    where the problem occured.  When this exception is a result of
    constructor mis-use in Python code, the traceback will tell you
    where the problem lies.
    """

    type = None
    """The abstract L{pyxb.binding.basis.complexTypeDefinition} subclass used."""

    node = None
    """The L{xml.dom.Element} from which instantiation was attempted, if available."""

    def __init__ (self, type, location, node):
        """@param type: the value for the L{type} attribute.
        @param location: the value for the L{location} attribute.
        @param node: the value for the L{node} attribute."""
        self.type = type
        self.location = location
        self.node = node
        super(AbstractInstantiationError, self).__init__(type, location, node)

    def __str__ (self):
        # If the type is abstract, it has to have a name.
        return 'Cannot instantiate abstract type %s directly' % (self.type._ExpandedName,)

class AttributeOnSimpleTypeError (ComplexTypeValidationError):
    """Attempt made to set an attribute on an element with simple type.

    Note that elements with complex type and simple content may have
    attributes; elements with simple type must not."""
    
    instance = None
    """The simple type binding instance on which no attributes exist."""

    tag = None
    """The name of the proposed attribute."""

    value = None
    """The value proposed to be assigned to the non-existent attribute."""
    
    def __init__ (self, instance, tag, value, location=None):
        """@param instance: the value for the L{instance} attribute.
        @param tag: the value for the L{tag} attribute.
        @param value: the value for the L{value} attribute.
        @param location: the value for the L{location} attribute.  Default taken from C{instance} if possible."""

        self.instance = instance
        self.tag = tag
        self.value = value
        if location is None:
            location = self.instance._location()
        self.location = location
        super(AttributeOnSimpleTypeError, self).__init__(instance, tag, value, location)

    def __str__ (self):
        return 'Simple type %s cannot support attribute %s' % (self.instance._Name(), self.tag)

class ContentValidationError (ComplexTypeValidationError):
    """Violation of a complex type content model."""
    pass

class SimpleContentAbsentError (ContentValidationError):
    """An instance with simple content was not provided with a value."""

    instance = None
    """The binding instance for which simple content is missing."""

    def __init__ (self, instance, location):
        """@param instance: the value for the L{instance} attribute.
        @param location: the value for the L{location} attribute."""
        self.instance = instance
        self.location = location
        super(SimpleContentAbsentError, self).__init__(instance, location)

    def __str__ (self):
        return 'Type %s requires content' % (self.instance._Name(),)

class ExtraSimpleContentError (ContentValidationError):
    """A complex type with simple content was provided too much content."""

    instance = None
    """The binding instance that already has simple content assigned."""

    value = None
    """The proposed addition to that simple content."""

    def __init__ (self, instance, value, location=None):
        """@param instance: the value for the L{instance} attribute.
        @param value: the value for the L{value} attribute.
        @param location: the value for the L{location} attribute."""
        self.instance = instance
        self.value = value
        self.location = location
        super(ExtraSimpleContentError, self).__init__(instance, value, location)

    def __str__ (self):
        return 'Instance of %s already has simple content value assigned' % (self.instance._Name(),)

class MixedContentError (ContentValidationError):
    """Non-element content added to a complex type instance that does not support mixed content."""
    
    instance = None
    """The binding instance."""

    value = None
    """The non-element content."""

    def __init__ (self, instance, value, location=None):
        """@param instance: the value for the L{instance} attribute.
        @param value: the value for the L{value} attribute.
        @param location: the value for the L{location} attribute."""
        self.instance = instance
        self.value = value
        self.location = location
        super(MixedContentError, self).__init__(instance, value, location)

    def __str__ (self):
        if self.location is not None:
            return 'Invalid non-element content at %s' % (self.location,)
        return 'Invalid non-element content'

class UnprocessedKeywordContentError (ContentValidationError):
    """A complex type constructor was provided with keywords that could not be recognized."""

    instance = None
    """The binding instance being constructed."""

    keywords = None
    """The keywords that could not be recognized.  These may have been
    intended to be attributes or elements, but cannot be identified as
    either."""

    def __init__ (self, instance, keywords, location=None):
        """@param instance: the value for the L{instance} attribute.
        @param keywords: the value for the L{keywords} attribute.
        @param location: the value for the L{location} attribute."""
        self.instance = instance
        self.keywords = keywords
        self.location = location
        super(UnprocessedKeywordContentError, self).__init__(instance, keywords, location)

    def __str__ (self):
        return 'Unprocessed keywords instantiating %s: %s' % (self.instance._Name(), ' '.join(self.keywords.keys()))

class IncrementalElementContentError (ContentValidationError):
    """Element or element-like content could not be validly associated with an sub-element in the content model.

    This exception occurs when content is added to an element during
    incremental validation, such as when positional arguments are used
    in a constructor or material is appended either explicitly or
    through parsing a DOM instance."""

    instance = None
    """The binding for which the L{value} could not be associated with an element."""

    automaton_configuration = None
    """The L{pyxb.binding.content.AutomatonConfiguration} representing the current state of the L{instance} content."""

    value = None
    """The value that could not be associated with allowable content."""
    
    def __init__ (self, instance, automaton_configuration, value, location=None):
        """@param instance: the value for the L{instance} attribute.
        @param automaton_configuration: the value for the L{automaton_configuration} attribute.
        @param value: the value for the L{value} attribute.
        @param location: the value for the L{location} attribute."""
        self.instance = instance
        self.automaton_configuration = automaton_configuration
        self.value = value
        self.location = location
        super(IncrementalElementContentError, self).__init__(instance, automaton_configuration, value, location)

class UnrecognizedContentError (IncrementalElementContentError):
    """Element or element-like content could not be validly associated with an sub-element in the content model.

    This exception occurs when content is added to an element during incremental validation."""

    def __str__ (self):
        value = self.value
        try:
            value = str(self.value._element().name())
        except:
            pass
        acceptable = self.automaton_configuration.acceptableContent()
        if 0 == acceptable:
            expect = 'no more content'
        else:
            import pyxb.binding.content
            seen = set()
            names = []
            for u in acceptable:
                if isinstance(u, pyxb.binding.content.ElementUse):
                    n = str(u.elementBinding().name())
                else:
                    assert isinstance(u, pyxb.binding.content.WildcardUse)
                    n = 'xs:any'
                if not (n in seen):
                    names.append(n)
                    seen.add(n)
            expect = ' or '.join(names)
        location = ''
        if self.location is not None:
            location = ' at %s' % (self.location,)
        return 'Invalid content %s%s (expect %s)' % (value, location, expect)
        
    def details (self):
        import pyxb.binding.basis
        import pyxb.binding.content
        i = self.instance
        rv = [ ]
        if i._element() is not None:
            rv.append('The containing element %s is defined at %s.' % (i._element().name(), i._element().xsdLocation()))
        rv.append('The containing element type %s is defined at %s' % (self.instance._Name(), str(self.instance._XSDLocation)))
        if self.location is not None:
            rv.append('The unrecognized content %s begins at %s' % (self.value._diagnosticName(), self.location))
        else:
            rv.append('The unrecognized content is %s' % (self.value._diagnosticName(),))
        ty = type(self.instance)
        rv.append('The %s automaton %s in an accepting state.' % (self.instance._Name(), self.automaton_configuration.isAccepting() and "is" or "is not"))
        if isinstance(self.instance, pyxb.binding.basis.complexTypeDefinition) and self.instance._IsMixed():
            rv.append('Character information content would be permitted.')
        acceptable = self.automaton_configuration.acceptableContent()
        if 0 == len(acceptable):
            rv.append('No elements or wildcards would be accepted at this point.')
        else:
            rv.append('The following element and wildcard content would be accepted:')
            rv2 = []
            for u in acceptable:
                if isinstance(u, pyxb.binding.content.ElementUse):
                    rv2.append('An element %s per %s' % (u.elementBinding().name(), u.xsdLocation()))
                else:
                    assert isinstance(u, pyxb.binding.content.WildcardUse)
                    rv2.append('A wildcard per %s' % (u.xsdLocation(),))
            rv.append('\t' + '\n\t'.join(rv2))
        return '\n'.join(rv)

class BatchElementContentError (ContentValidationError):
    """Element/wildcard content cannot be reconciled with the required content model.

    This exception occurs in post-construction validation using a
    fresh validating automaton."""
    
    instance = None
    """The binding instance being constructed."""

    automaton_configuration = None
    """The L{pyxb.binding.content.AutomatonConfiguration} representing the current state of the L{instance} content."""

    symbols = None
    """The sequence of symbols that were accepted as content prior to the error."""

    symbol_set = None
    """The leftovers from L{pyxb.binding.basis.complexTypeDefinition._symbolSet} that could not be reconciled with the content model."""

    def __init__ (self, instance, automaton_configuration, symbols, symbol_set):
        """@param instance: the value for the L{instance} attribute.
        @param automaton_configuration: the value for the L{automaton_configuration} attribute.
        @param symbols: the value for the L{symbols} attribute.
        @param symbol_set: the value for the L{symbol_set} attribute."""
        self.instance = instance
        self.automaton_configuration = automaton_configuration
        self.symbols = symbols
        self.symbol_set = symbol_set
        super(BatchElementContentError, self).__init__(instance, automaton_configuration, symbols, symbol_set)

class IncompleteElementContentError (BatchElementContentError):
    """Validation of an instance failed to produce an accepting state.

    This exception occurs in batch-mode validation."""
    pass

class UnprocessedElementContentError (BatchElementContentError):
    """Validation of an instance produced an accepting state but left element material unconsumed.

    This exception occurs in batch-mode validation."""
    pass

class SimpleTypeValueError (ValidationError):
    """Raised when a simple type value does not satisfy its constraints."""
    type = None
    """The L{pyxb.binding.basis.simpleTypeDefinition} that constrains values."""
    
    value = None
    """The value that violates the constraints of L{type}.  In some
    cases this is a tuple of arguments passed to a constructor that
    failed with a built-in exception likeC{ValueError} or
    C{OverflowError}."""

    def __init__ (self, type, value):
        """@param type: the value for the L{type} attribute.
        @param value: the value for the L{value} attribute.
        """
        self.type = type
        self.value = value
        super(SimpleTypeValueError, self).__init__(type, value)

class SimpleListValueError (SimpleTypeValueError):
    """Raised when a list simple type contains a member that does not satisfy its constraints.

    In this case, L{type} is the type of the list, and the value
    C{type._ItemType} is the type for which the value is
    unacceptable."""
    pass

class SimpleUnionValueError (SimpleTypeValueError):
    """Raised when a union simple type contains a member that does not satisfy its constraints.

    In this case, L{type} is the type of the union, and the value
    C{type._MemberTypes} is the set of types for which the value is
    unacceptable."""
    pass

class SimpleFacetValueError (SimpleTypeValueError):
    """Raised when a simple type value does not satisfy a facet constraint.

    This extends L{SimpleTypeValueError} with the L{facet} field which
    can be used to determine why the value is unacceptable."""

    type = None
    """The L{pyxb.binding.basis.simpleTypeDefinition} that constrains values."""
    
    value = None
    """The value that violates the constraints of L{type}.  In some
    cases this is a tuple of arguments passed to a constructor that
    failed with a built-in exception likeC{ValueError} or
    C{OverflowError}."""

    facet = None
    """The specific facet that is violated by the value."""

    def __init__ (self, type, value, facet):
        """@param type: the value for the L{type} attribute.
        @param value: the value for the L{value} attribute.
        """
        self.type = type
        self.value = value
        self.facet = facet
        # Bypass immediate parent
        super(SimpleTypeValueError, self).__init__(type, value, facet)

    def __str__ (self):
        return 'Type %s %s constraint violated by value %s' % (self.type, self.facet._Name, self.value)

class SimplePluralValueError (SimpleTypeValueError):
    """Raised when context requires a plural value.

    Unlike L{SimpleListValueError}, in this case the plurality is
    external to C{type}, for example when an element has simple
    content and allows multiple occurrences."""
    pass

class AttributeValidationError (ValidationError):
    """Raised when an attribute requirement is not satisfied."""

    type = None
    """The L{pyxb.binding.basis.complexTypeDefinition} subclass of the instance."""

    tag = None
    """The name of the attribute."""
    
    instance = None
    """The binding instance, if available."""

    def __init__ (self, type, tag, instance=None, location=None):
        """@param type: the value for the L{type} attribute.
        @param tag: the value for the L{tag} attribute.
        @param instance: the value for the L{instance} attribute.
        @param location: the value for the L{location} attribute.  Default taken from C{instance} if possible.
        """
        import pyxb.utils.utility as utility
        self.type = type
        self.tag = tag
        self.instance = instance
        if (location is None) and isinstance(instance, utility.Locatable_mixin):
            location = instance._location()
        self.location = location
        super(AttributeValidationError, self).__init__(type, tag, instance, location)

class UnrecognizedAttributeError (AttributeValidationError):
    """Attempt to reference an attribute not sanctioned by content model."""
    pass

class ProhibitedAttributeError (AttributeValidationError):
    """Raised when an attribute that is prohibited is set or referenced in an element."""
    def __str__ (self):
        return 'Attempt to reference prohibited attribute %s in type %s' % (self.tag, self.type)

class MissingAttributeError (AttributeValidationError):
    """Raised when an attribute that is required is missing in an element."""
    def __str__ (self):
        return 'Instance of %s lacks required attribute %s' % (self.type, self.tag)

class AttributeChangeError (AttributeValidationError):
    """Attempt to change an attribute that has a fixed value constraint."""
    def __str__ (self):
        return 'Cannot change fixed attribute %s in type %s' % (self.tag, self.type)

class NoNillableSupportError (PyXBException):
    """Raised when checking _isNil on a type that does not support nillable."""

    instance = None
    """The binding instance on which an inappropriate operation was invoked."""

    def __init__ (self, instance):
        """@param instance: the binding instance that was mis-used.
        This will be available in the L{instance} attribute."""
        self.instance = instance
        super(NoNillableSupportError, self).__init__(instance)

class ContentInNilInstanceError (PyXBException):
    """Raised when an element that is marked to be nil is assigned content."""

    instance = None
    """The binding instance which is xsi:nil"""

    content = None
    """The content that was to be assigned to the instance."""

    def __init__ (self, instance, content):
        """@param instance: the binding instance that is marked nil.
        This will be available in the L{instance} attribute.

        @param content: the content found to be in violation of the nil requirement.
        This will be available in the L{content} attribute.

        """
        self.instance = instance
        self.content = content
        super(ContentInNilInstanceError, self).__init__(instance, content)

class BindingError (PyXBException):
    """Raised when the bindings are mis-used.

    These are not validation errors, but rather structural errors.
    For example, attempts to extract complex content from a type that
    requires simple content, or vice versa.  """

class NotSimpleContentError (BindingError):
    """An operation that requires simple content was invoked on a
    complex type instance that does not have simple content."""

    instance = None
    """The binding instance which should have had simple content."""

    def __init__ (self, instance):
        """@param instance: the binding instance that was mis-used.
        This will be available in the L{instance} attribute."""
        self.instance = instance
        super(BindingError, self).__init__(instance)
    pass

    def __str__ (self):
        return 'type %s does not have simple content' % (self.instance._Name(),)

class NotComplexContentError (BindingError):
    """An operation that requires a content model was invoked on a
    complex type instance that has empty or simple content."""

    instance = None
    """The binding instance which should have had a content model."""

    def __init__ (self, instance):
        """@param instance: the binding instance that was mis-used.
        This will be available in the L{instance} attribute."""
        self.instance = instance
        super(BindingError, self).__init__(instance)

    def __str__ (self):
        return 'type %s has simple/empty content' % (self.instance._Name(),)

class ReservedNameError (BindingError):
    """Reserved name set in binding instance."""

    instance = None
    """The binding instance."""

    name = None
    """The name that was caught being assigned"""

    def __init__ (self, instance, name):
        """@param instance: the value for the L{instance} attribute.
        p@param name: the value for the L{name} attribute."""
        self.instance = instance
        self.name = name
        super(ReservedNameError, self).__init__(instance, name)

    def __str__ (self):
        return '%s is a reserved name within %s' % (self.name, self.instance._Name())

class PyXBError (exceptions.Exception):
    """Base class for exceptions that indicate a problem that the user probably can't fix."""
    pass
    
class UsageError (PyXBError):
    """Raised when the code detects user violation of an API."""

class LogicError (PyXBError):
    """Raised when the code detects an implementation problem."""

class IncompleteImplementationError (LogicError):
    """Raised when required capability has not been implemented.

    This is only used where it is reasonable to expect the capability
    to be present, such as a feature of XML schema that is not
    supported (e.g., the redefine directive)."""
