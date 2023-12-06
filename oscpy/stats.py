"Simple utility class to gather stats about the volumes of data managed"

from collections import Counter


class Stats(object):
    def __init__(self, calls=0, bytes=0, params=0, types=None, **kwargs):
        self.calls = calls
        self.bytes = bytes
        self.params = params
        self.types = types or Counter()
        super(Stats, self).__init__(**kwargs)

    def to_tuple(self):
        types = self.types
        keys = types.keys()
        return (
            self.calls,
            self.bytes,
            self.params,
            ''.join(keys),
        ) + tuple(types[k] for k in keys)

    def __iadd__(self, other):
        assert isinstance(other, Stats)
        self.calls += other.calls
        self.bytes += other.bytes
        self.params += other.params
        self.types += other.types
        return self

    def __add__(self, other):
        assert isinstance(other, Stats)
        return Stats(
            calls=self.calls + other.calls,
            bytes=self.bytes + other.bytes,
            params=self.params + other.params,
            types=self.types + other.types
        )

    def __eq__(self, other):
        return other is self or (
            isinstance(other, Stats)
            and self.calls == self.calls
            and self.bytes == self.bytes
            and self.params == self.params
            and self.types == other.types
        )

    def __repr__(self):
        return 'Stats:\n' + '\n'.join(
            '    {}:{}{}'.format(
                k,
                '' if isinstance(v, str) and v.startswith('\n') else ' ',
                v
            )
            for k, v in (
                ('calls', self.calls),
                ('bytes', self.bytes),
                ('params', self.params),
                (
                    'types',
                    ''.join(
                        '\n        {}: {}'.format(k, self.types[k])
                        for k in sorted(self.types)
                    )
                )
            )
        )
