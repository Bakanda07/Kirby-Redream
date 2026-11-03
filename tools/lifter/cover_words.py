# which words the lifter rejects, by reason (run from TomodachiLife-recomp/tools/lifter with RECOMP_BIN set)
import collections, os, struct, sys
sys.path.insert(0, os.getcwd())
sys.argv = ['recomp.py']
import recomp as R
fn = R.Fn(R.BASE, R.BASE + R.TEXT_SIZE, R.Env())
fn.env.imports = set()
seen = collections.defaultdict(collections.Counter)
for (w,) in struct.iter_unpack('<I', R.IMG[R.FILE_OFF:R.FILE_OFF + R.TEXT_SIZE]):
    try:
        fn.lift(w, R.BASE + 0x1000000)
    except R.Unimpl as e:
        seen[str(e)][w] += 1
    except Exception:
        seen['error'][w] += 1
for r, c in seen.items():
    print(r, sum(c.values()), 'distinct', len(c), ' '.join('%08x:%d' % kv for kv in c.most_common(8)))
