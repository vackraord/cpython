"""Support code for packaging test cases.

A few helper classes are provided: LoggingCatcher, TempdirManager and
EnvironRestorer. They are written to be used as mixins::

    from packaging.tests import unittest
    from packaging.tests.support import LoggingCatcher

    class SomeTestCase(LoggingCatcher, unittest.TestCase):

If you need to define a setUp method on your test class, you have to
call the mixin class' setUp method or it won't work (same thing for
tearDown):

        def setUp(self):
            super(SomeTestCase, self).setUp()
            ... # other setup code

Also provided is a DummyCommand class, useful to mock commands in the
tests of another command that needs them, a create_distribution function
and a skip_unless_symlink decorator.

Also provided is a DummyCommand class, useful to mock commands in the
tests of another command that needs them, a create_distribution function
and a skip_unless_symlink decorator.

Each class or function has a docstring to explain its purpose and usage.
"""

import os
import shutil
import logging
import weakref
import tempfile

from packaging.dist import Distribution
from packaging.tests import unittest
from test.support import requires_zlib, unlink

__all__ = ['LoggingCatcher', 'TempdirManager', 'EnvironRestorer',
           'DummyCommand', 'unittest', 'create_distribution',
           'skip_unless_symlink', 'requires_zlib']


logger = logging.getLogger('packaging')
logger2to3 = logging.getLogger('RefactoringTool')


class _TestHandler(logging.handlers.BufferingHandler):
    # stolen and adapted from test.support

    def __init__(self):
        logging.handlers.BufferingHandler.__init__(self, 0)
        self.setLevel(logging.DEBUG)

    def shouldFlush(self):
        return False

    def emit(self, record):
        self.buffer.append(record)


class LoggingCatcher:
    """TestCase-compatible mixin to receive logging calls.

    Upon setUp, instances of this classes get a BufferingHandler that's
    configured to record all messages logged to the 'packaging' logger.

    Use get_logs to retrieve messages and self.loghandler.flush to discard
    them.  get_logs automatically flushes the logs; if you test code that
    generates logging messages but don't use get_logs, you have to flush
    manually before doing other checks on logging message, otherwise you
    will get irrelevant results.  See example in test_command_check.
    """

    def setUp(self):
        super(LoggingCatcher, self).setUp()
        self.loghandler = handler = _TestHandler()
        self._old_levels = logger.level, logger2to3.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)  # we want all messages
        logger2to3.setLevel(logging.CRITICAL)  # we don't want 2to3 messages

    def tearDown(self):
        handler = self.loghandler
        # All this is necessary to properly shut down the logging system and
        # avoid a regrtest complaint.  Thanks to Vinay Sajip for the help.
        handler.close()
        logger.removeHandler(handler)
        for ref in weakref.getweakrefs(handler):
            logging._removeHandlerRef(ref)
        del self.loghandler
        logger.setLevel(self._old_levels[0])
        logger2to3.setLevel(self._old_levels[1])
        super(LoggingCatcher, self).tearDown()

    def get_logs(self, *levels):
        """Return all log messages with level in *levels*.

        Without explicit levels given, returns all messages.  *levels* defaults
        to all levels.  For log calls with arguments (i.e.
        logger.info('bla bla %r', arg)), the messages will be formatted before
        being returned (e.g. "bla bla 'thing'").

        Returns a list.  Automatically flushes the loghandler after being
        called.

        Example: self.get_logs(logging.WARN, logging.DEBUG).
        """
        if not levels:
            messages = [log.getMessage() for log in self.loghandler.buffer]
        else:
            messages = [log.getMessage() for log in self.loghandler.buffer
                        if log.levelno in levels]
        self.loghandler.flush()
        return messages


class TempdirManager:
    """TestCase-compatible mixin to create temporary directories and files.

    Directories and files created in a test_* method will be removed after it
    has run.
    """

    def setUp(self):
        super(TempdirManager, self).setUp()
        self._olddir = os.getcwd()
        self._basetempdir = tempfile.mkdtemp()
        self._files = []

    def tearDown(self):
        for handle, name in self._files:
            handle.close()
            unlink(name)

        os.chdir(self._olddir)
        shutil.rmtree(self._basetempdir)
        super(TempdirManager, self).tearDown()

    def mktempfile(self):
        """Create a read-write temporary file and return it."""
        fd, fn = tempfile.mkstemp(dir=self._basetempdir)
        os.close(fd)
        fp = open(fn, 'w+')
        self._files.append((fp, fn))
        return fp

    def mkdtemp(self):
        """Create a temporary directory and return its path."""
        d = tempfile.mkdtemp(dir=self._basetempdir)
        return d

    def write_file(self, path, content='xxx', encoding=None):
        """Write a file at the given path.

        path can be a string, a tuple or a list; if it's a tuple or list,
        os.path.join will be used to produce a path.
        """
        if isinstance(path, (list, tuple)):
            path = os.path.join(*path)
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)

    def create_dist(self, **kw):
        """Create a stub distribution object and files.

        This function creates a Distribution instance (use keyword arguments
        to customize it) and a temporary directory with a project structure
        (currently an empty directory).

        It returns the path to the directory and the Distribution instance.
        You can use self.write_file to write any file in that
        directory, e.g. setup scripts or Python modules.
        """
        if 'name' not in kw:
            kw['name'] = 'foo'
        tmp_dir = self.mkdtemp()
        project_dir = os.path.join(tmp_dir, kw['name'])
        os.mkdir(project_dir)
        dist = Distribution(attrs=kw)
        return project_dir, dist

    def assertIsFile(self, *args):
        path = os.path.join(*args)
        dirname = os.path.dirname(path)
        file = os.path.basename(path)
        if os.path.isdir(dirname):
            files = os.listdir(dirname)
            msg = "%s not found in %s: %s" % (file, dirname, files)
            assert os.path.isfile(path), msg
        else:
            raise AssertionError(
                    '%s not found. %s does not exist' % (file, dirname))

    def assertIsNotFile(self, *args):
        path = os.path.join(*args)
        self.assertFalse(os.path.isfile(path), "%r exists" % path)


class EnvironRestorer:
    """TestCase-compatible mixin to restore or delete environment variables.

    The variables to restore (or delete if they were not originally present)
    must be explicitly listed in self.restore_environ.  It's better to be
    aware of what we're modifying instead of saving and restoring the whole
    environment.
    """

    def setUp(self):
        super(EnvironRestorer, self).setUp()
        self._saved = []
        self._added = []
        for key in self.restore_environ:
            if key in os.environ:
                self._saved.append((key, os.environ[key]))
            else:
                self._added.append(key)

    def tearDown(self):
        for key, value in self._saved:
            os.environ[key] = value
        for key in self._added:
            os.environ.pop(key, None)
        super(EnvironRestorer, self).tearDown()


class DummyCommand:
    """Class to store options for retrieval via set_undefined_options().

    Useful for mocking one dependency command in the tests for another
    command, see e.g. the dummy build command in test_build_scripts.
    """

    def __init__(self, **kwargs):
        for kw, val in kwargs.items():
            setattr(self, kw, val)

    def ensure_finalized(self):
        pass


class TestDistribution(Distribution):
    """Distribution subclasses that avoids the default search for
    configuration files.

    The ._config_files attribute must be set before
    .parse_config_files() is called.
    """

    def find_config_files(self):
        return self._config_files


def create_distribution(configfiles=()):
    """Prepares a distribution with given config files parsed."""
    d = TestDistribution()
    d.config.find_config_files = d.find_config_files
    d._config_files = configfiles
    d.parse_config_files()
    d.parse_command_line()
    return d


def fake_dec(*args, **kw):
    """Fake decorator"""
    def _wrap(func):
        def __wrap(*args, **kw):
            return func(*args, **kw)
        return __wrap
    return _wrap


try:
    from test.support import skip_unless_symlink
except ImportError:
    skip_unless_symlink = unittest.skip(
        'requires test.support.skip_unless_symlink')