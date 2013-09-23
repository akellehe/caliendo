from contextlib import contextmanager
from caliendo.facade import cache

def _dot_lookup(thing, comp, import_path):
    """
    Import one attribute from an imported module at the end of it's dot path. 
   
    :rtype <module>: 
    """
    try:
        return getattr(thing, comp)
    except AttributeError:
        __import__(import_path)
        return getattr(thing, comp)

def _importer(target):
    """
    Imports a target along a dot path.

    :rtype mixed: An imported module or member
    """
    components = target.split('.')
    import_path = components.pop(0)
    thing = __import__(import_path)

    for comp in components:
        import_path += ".%s" % comp 
        thing = _dot_lookup(thing, comp, import_path)
    return thing

def _get_target(target):
    """
    Returns an imported module referenced along a dot path and the attribute 
    name to reference a method or class. 
    
    :rtype tuple(module, str):
    """
    try:
        target, attribute = target.rsplit('.', 1)
    except (TypeError, ValueError):
        raise TypeError("Need a valid target to patch. You supplied: %r" %
                        (target,))
    return _importer(target), attribute

@contextmanager
def patch_in_place(import_path, rvalue=None):
    """
    Patches an attribute of a module referenced on import_path with a decorated 
    version that will use the caliendo cache if rvalue is None. Otherwise it will
    patch the attribute of the module to return rvalue when called.
    
    This method provides a context in which to use the patched module. After the
    decorated method is called patch_in_place unpatches the patched module with 
    the original method.
    
    :param str import_path: The import path of the method to patch.
    :param mixed rvalue: The return value of the patched method.
    
    :rtype None:
    """
    try:
        getter, attribute = _get_target(import_path)
        original = getattr(getter, attribute)
        if rvalue == None:
            setattr(getter, attribute, lambda *args, **kwargs: cache(handle=original, args=args, kwargs=kwargs))
        else:
            setattr(getter, attribute, lambda *args, **kwargs: rvalue)
        yield None
    except:
        setattr(getter, attribute, original)
    finally:
        setattr(getter, attribute, original)

def patch(import_path, rvalue=None): # Need to undo the patch after exiting the decorated method.
    """
    External interface to patch functionality. patch is a decorator for a test.
    When patch decorates a test it replaces the method on the import_path with 
    a version decorated by the caliendo cache or a lambda in the event rvalue is 
    not None.
    
    Patch offers a context to the test that uses the patched method. After the
    test exits the context the method is unpatched.
    
    :param str import_path: The import path for the method to patch.
    :param mixed rvalue: The return value of the patched method.
    
    :rtype lambda: The patched test.
    """
    def patch_test(unpatched_test):
        def patched_test(*args, **kwargs): 
            with patch_in_place(import_path, rvalue) as nothing:
                unpatched_test()
        return patched_test

    return lambda unpatched_test: patch_test(unpatched_test) 