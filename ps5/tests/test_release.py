"""Source releases must fail closed on private files and damaged manifests."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec=importlib.util.spec_from_file_location('release_validator',Path(__file__).parents[1]/'tools/validate.py')
validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)

class ReleaseValidation(unittest.TestCase):
    def archive(self, extra=None, corrupt=False):
        root=Path(self.directory.name)/'release.zip'
        files={name:b'source' for name in ['README.md','LICENSE','ps5/README.md','ps5/tools/build.py','ps5/tools/setup-deps.py','ps5/dependencies.json']}
        if extra:files[extra]=b'not for distribution'
        rows=[{'path':p,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()} for p,b in files.items()]
        with zipfile.ZipFile(root,'w') as z:
            for p,b in files.items():z.writestr(p,b+b'changed' if corrupt and p=='README.md' else b)
            z.writestr('RELEASE-MANIFEST.json',json.dumps({'commit':'test','files':rows}))
        return root
    def setUp(self):self.directory=tempfile.TemporaryDirectory()
    def tearDown(self):self.directory.cleanup()
    def test_valid_source(self):
        with contextlib.redirect_stdout(io.StringIO()):validator.validate_archive(self.archive())
    def test_hash_mismatch(self):
        with self.assertRaisesRegex(ValueError,'Hash mismatch'):validator.validate_archive(self.archive(corrupt=True))
    def test_private_files_and_paths(self):
        for name in ['libgamecode.a','renamed-game.a','objects/game.o','game/code/cking.rpx','game.key','eboot.bin','states/slot1.bin','capture.png','build/gen/code.c','../escape.txt','/absolute.txt']:
            with self.subTest(name=name),self.assertRaises(ValueError):validator.validate_archive(self.archive(extra=name))

if __name__=='__main__':unittest.main()
