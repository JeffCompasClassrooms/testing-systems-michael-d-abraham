import os
import pickle
import pytest
from mydb import MyDB


def describe_MyDB():

    def describe_init():

        def it_creates_new_file_when_file_does_not_exist(tmp_path):
            test_file = tmp_path / "test_init_new.db"
            assert not os.path.exists(test_file)
            
            db = MyDB(str(test_file))
            
            assert os.path.exists(test_file)
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == []

        def it_uses_existing_file_when_file_exists(tmp_path):
            test_file = tmp_path / "test_init_existing.db"
            existing_data = ["existing_string_1", "existing_string_2"]
            with open(test_file, 'wb') as f:
                pickle.dump(existing_data, f)
            
            db = MyDB(str(test_file))
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == existing_data

        def it_stores_filename_in_instance_variable(tmp_path):
            test_file = tmp_path / "test_init_fname.db"
            db = MyDB(str(test_file))
            assert db.fname == str(test_file)

    def describe_loadStrings():

        def it_loads_empty_array_from_new_database(tmp_path):
            test_file = tmp_path / "test_load_empty.db"
            db = MyDB(str(test_file))
            result = db.loadStrings()
            assert result == []

        def it_loads_single_string_from_database(tmp_path):
            test_file = tmp_path / "test_load_single.db"
            test_data = ["single_string"]
            with open(test_file, 'wb') as f:
                pickle.dump(test_data, f)
            db = MyDB(str(test_file))
            
            result = db.loadStrings()
            assert result == ["single_string"]

        def it_loads_multiple_strings_from_database(tmp_path):
            test_file = tmp_path / "test_load_multiple.db"
            test_data = ["first", "second", "third", "fourth"]
            with open(test_file, 'wb') as f:
                pickle.dump(test_data, f)
            db = MyDB(str(test_file))
            
            result = db.loadStrings()
            assert result == test_data
            assert len(result) == 4

        def it_preserves_string_content_and_order(tmp_path):
            test_file = tmp_path / "test_load_special.db"
            test_data = ["", "spaces  here", "line\nbreak", "tab\there", "unicode: 你好", "123"]
            with open(test_file, 'wb') as f:
                pickle.dump(test_data, f)
            db = MyDB(str(test_file))
            
            result = db.loadStrings()
            assert result == test_data

    def describe_saveStrings():

        def it_saves_empty_array_to_file(tmp_path):
            test_file = tmp_path / "test_save_empty.db"
            db = MyDB(str(test_file))
            
            db.saveStrings([])
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == []

        def it_saves_single_string_to_file(tmp_path):
            test_file = tmp_path / "test_save_single.db"
            db = MyDB(str(test_file))
            test_data = ["only_one_string"]
            
            db.saveStrings(test_data)
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == test_data

        def it_saves_multiple_strings_to_file(tmp_path):
            test_file = tmp_path / "test_save_multiple.db"
            db = MyDB(str(test_file))
            test_data = ["alpha", "beta", "gamma", "delta"]
            
            db.saveStrings(test_data)
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == test_data
            assert len(content) == 4

        def it_overwrites_existing_data(tmp_path):
            test_file = tmp_path / "test_save_overwrite.db"
            initial_data = ["old1", "old2", "old3"]
            with open(test_file, 'wb') as f:
                pickle.dump(initial_data, f)
            db = MyDB(str(test_file))
            
            new_data = ["new1", "new2"]
            db.saveStrings(new_data)
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == new_data
            assert len(content) == 2

        def it_preserves_string_characteristics(tmp_path):
            test_file = tmp_path / "test_save_special.db"
            db = MyDB(str(test_file))
            test_data = ["", "  spaces  ", "new\nline", "\ttab", "unicode: 世界", "!@#$%^&*()"]
            
            db.saveStrings(test_data)
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == test_data

    def describe_saveString():

        def it_appends_string_to_empty_database(tmp_path):
            test_file = tmp_path / "test_append_to_empty.db"
            db = MyDB(str(test_file))
            
            db.saveString("first_string")
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == ["first_string"]

        def it_appends_string_to_existing_data(tmp_path):
            test_file = tmp_path / "test_append_to_existing.db"
            initial_data = ["existing1", "existing2"]
            with open(test_file, 'wb') as f:
                pickle.dump(initial_data, f)
            db = MyDB(str(test_file))
            
            db.saveString("new_string")
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == ["existing1", "existing2", "new_string"]

        def it_appends_multiple_strings_sequentially(tmp_path):
            test_file = tmp_path / "test_append_multiple.db"
            db = MyDB(str(test_file))
            
            db.saveString("first")
            db.saveString("second")
            db.saveString("third")
            db.saveString("fourth")
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == ["first", "second", "third", "fourth"]

        def it_preserves_empty_string(tmp_path):
            test_file = tmp_path / "test_append_empty.db"
            db = MyDB(str(test_file))
            db.saveString("before")
            
            db.saveString("")
            db.saveString("after")
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == ["before", "", "after"]

        def it_preserves_special_characters_in_appended_string(tmp_path):
            test_file = tmp_path / "test_append_special.db"
            db = MyDB(str(test_file))
            
            db.saveString("line\nbreak")
            db.saveString("tab\there")
            db.saveString("unicode: こんにちは")
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content[0] == "line\nbreak"
            assert content[1] == "tab\there"
            assert content[2] == "unicode: こんにちは"

        def it_persists_data_across_multiple_operations(tmp_path):
            test_file = tmp_path / "test_persist_operations.db"
            db = MyDB(str(test_file))
            db.saveStrings(["initial1", "initial2"])
            
            loaded = db.loadStrings()
            assert loaded == ["initial1", "initial2"]
            
            db.saveString("appended1")
            loaded = db.loadStrings()
            assert loaded == ["initial1", "initial2", "appended1"]
            
            db.saveStrings(["replaced1", "replaced2", "replaced3"])
            loaded = db.loadStrings()
            assert loaded == ["replaced1", "replaced2", "replaced3"]
            
            db.saveString("final")
            
            with open(test_file, 'rb') as f:
                content = pickle.load(f)
            assert content == ["replaced1", "replaced2", "replaced3", "final"]
