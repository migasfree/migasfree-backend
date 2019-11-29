# https://github.com/andymccurdy/django-tips-and-tricks/blob/master/model_update.py
# http://www.slideshare.net/andymccurdy/django-tips-andtricks-1

import operator

from django.db.models.expressions import F, Expression
from six import iteritems

EXPRESSION_NODE_CALLBACKS = {
    Expression.ADD: operator.add,
    Expression.SUB: operator.sub,
    Expression.MUL: operator.mul,
    Expression.DIV: operator.truediv,
    Expression.MOD: operator.mod,
    # Expression.AND: operator.and_,
    # Expression.OR: operator.or_,
}


class CannotResolve(Exception):
    pass


def _resolve(instance, node):
    if isinstance(node, F):
        return getattr(instance, node.name)
    elif isinstance(node, Expression):
        return _resolve(instance, node)
    return node


def resolve_expression_node(instance, node):
    op = EXPRESSION_NODE_CALLBACKS.get(node.connector, None)
    if not op:
        raise CannotResolve
    runner = _resolve(instance, node.children[0])
    for n in node.children[1:]:
        runner = op(runner, _resolve(instance, n))
    return runner


def update(instance, **kwargs):
    """
    Atomically update instance, setting field/value pairs from kwargs
    fields that use auto_now=True should be updated corrected, too!
    """
    for field in instance._meta.fields:
        if hasattr(field, 'auto_now') and field.auto_now and field.name not in kwargs:
            kwargs[field.name] = field.pre_save(instance, False)

    rows_affected = instance.__class__._default_manager.filter(pk=instance.pk).update(**kwargs)

    # apply the updated args to the instance to mimic the change
    # note that these might slightly differ from the true database values
    # as the DB could have been updated by another thread. callers should
    # retrieve a new copy of the object if up-to-date values are required
    for k, v in iteritems(kwargs):
        if isinstance(v, Expression):
            v = resolve_expression_node(instance, v)
        setattr(instance, k, v)

    # If you use an ORM cache, make sure to invalidate the instance!
    # cache.set(djangocache.get_cache_key(instance=instance), None, 5)
    return rows_affected
