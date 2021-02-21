import unittest
from main import CommentHandler
from hashlib import sha256
from datetime import datetime

class CommentForm:
    def __init__(self):
        self.key_list=['redirect','post_id','comment-site','message','name','email']

    def keys(self):
        return self.key_list

    def get(self, key, default=None, type=None):
        return None

class TestKeyValidation(unittest.TestCase):
    def setUp(self):
        self.comment_form=CommentForm()
        self.dut=CommentHandler(self.comment_form)

    def test_valid_without_url(self):
        self.assertTrue(self.dut.validate_keys())

    def test_missing_key(self):
        self.comment_form.key_list.pop()
        self.assertFalse(self.dut.validate_keys())

    def test_valid_with_url(self):
        self.comment_form.key_list.append('url')
        self.assertTrue(self.dut.validate_keys())

    def test_extra_key(self):
        self.comment_form.key_list.append('extra')
        self.assertFalse(self.dut.validate_keys())

class TestGeneratedFields(unittest.TestCase):
    def test_id(self):
        dut=CommentHandler(CommentForm())
        hash=sha256()
        dut.data['post_id']="test"
        hash.update("test".encode("utf-8"))
        dut.data['name']="Test User"
        hash.update("Test User".encode("utf-8"))
        dut.data['message']="Hello World!"
        hash.update("Hello World!".encode("utf-8"))
        date=datetime.now()
        dut.data['date']=date
        hash.update(str(date).encode("utf-8"))
        self.assertEqual(dut.get_id(),hash.hexdigest())
    
    def test_gravatar(self):
        dut=CommentHandler(CommentForm())
        self.assertEqual(dut.get_gravatar("jautero@iki.fi"),"61f4730021b2869d7ad8babcfe790fbb")
        self.assertEqual(dut.get_gravatar("  jautero@iki.fi  "),"61f4730021b2869d7ad8babcfe790fbb")
        self.assertEqual(dut.get_gravatar("JAutero@iki.fi  "),"61f4730021b2869d7ad8babcfe790fbb")

class TestRedirectUrl(unittest.TestCase):
    def test_without_redirect(self):
        dut=CommentHandler(CommentForm())
        self.assertFalse(dut.get_redirect_url())

    def test_with_redirect(self):
        dut=CommentHandler({'redirect': 'https://www.google.com/'})
        self.assertEqual(dut.get_redirect_url(),'https://www.google.com/')

class TestConfiguration(unittest.TestCase):
    def test_simple_configuration(self):
        dut=CommentHandler(CommentForm(),"foo: bar")
        self.assertEqual(dut.config['foo'],'bar')