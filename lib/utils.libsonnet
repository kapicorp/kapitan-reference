// Generic Jsonnet utilities. We might want to propose most of these to the Jsonnet stdlib.

local id = function(value) value;

{
  objectGet(object, key, default=null):: if key in object then object[key] else default,
  objectHas(object, key, default=false):: if key in object && object[key] != null then true else default,

  objectValues(object):: [object[k] for k in std.objectFields(object)],

  mergeObjects(objects):: std.foldl(function(a, b) a + b, objects, {}),
  trace(object, text=''):: std.trace('Trace %s: %s' % [text, std.toString(object)], object),

  deepMerge(obj1, obj2)::
    local isIterable = function(value) $.arrayHas(['object', 'array'], std.type(value));

    assert isIterable(obj1) : 'obj1 must be iterable';
    assert isIterable(obj2) : 'obj2 must be iterable';
    assert std.type(obj1) == std.type(obj2) : 'obj1 and obj2 must be of the same type';

    obj1
    +
    obj2
    + (
      if std.type(obj1) == 'object' then {
        [k]: $.deepMerge(obj1[k], obj2[k])
        for k in std.objectFields(obj2)
        if k in obj1 && isIterable(obj1[k]) && isIterable(obj2[k])
      } else []
    )
  ,

  arrayHas(array, item):: [i for i in array if i == item] != [],

  // Report whether of the elements in `array` is true
  any(array, func=id):: [v for v in array if func(v)] != [],

  coalesce(values)::
    local non_null_values = [v for v in values if v != null];
    if non_null_values != [] then non_null_values[0] else null
  ,

  jsonSchema:: {
    nullable(objectSchema):: {
      anyOf: [objectSchema, { type: 'null' }],
    },
  },
}
