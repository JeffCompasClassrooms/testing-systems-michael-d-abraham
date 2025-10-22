import subprocess
import time
import json
import shutil
import sqlite3
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
import pytest
import signal
import os

BASE_URL = "http://127.0.0.1:8080"

class ServerFixture:
    def __init__(self):
        self.process = None
    
    def start(self):
        self.process = subprocess.Popen(
            ["python3", "squirrel_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        time.sleep(1.5)
        
        max_retries = 10
        for i in range(max_retries):
            try:
                urlopen(f"{BASE_URL}/squirrels", timeout=1)
                return
            except (URLError, HTTPError):
                if i < max_retries - 1:
                    time.sleep(0.5)
                else:
                    raise Exception("Server failed to start")
    
    def stop(self):
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except:
                    pass

@pytest.fixture(scope="session")
def server():
    srv = ServerFixture()
    srv.start()
    yield srv
    srv.stop()

@pytest.fixture(autouse=True)
def reset_database():
    shutil.copy("empty_squirrel_db.db", "squirrel_db.db")
    time.sleep(0.1)
    yield
    if os.path.exists("squirrel_db.db"):
        shutil.copy("empty_squirrel_db.db", "squirrel_db.db")

def make_request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    
    if data:
        data_encoded = urlencode(data).encode('utf-8')
    else:
        data_encoded = None
    
    request = Request(url, data=data_encoded, method=method)
    
    try:
        response = urlopen(request)
        status_code = response.getcode()
        headers = dict(response.headers)
        body = response.read().decode('utf-8')
        return {'status_code': status_code, 'headers': headers, 'body': body}
    except HTTPError as e:
        status_code = e.code
        headers = dict(e.headers)
        body = e.read().decode('utf-8')
        return {'status_code': status_code, 'headers': headers, 'body': body}

def get_db_records():
    conn = sqlite3.connect("squirrel_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM squirrels ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def describe_SquirrelServer_API():

    def describe_GET_squirrels_list():

        def it_returns_200_status_code_for_list_request(server):
            response = make_request('GET', '/squirrels')
            assert response['status_code'] == 200

        def it_returns_json_content_type_header_for_list(server):
            response = make_request('GET', '/squirrels')
            assert response['headers']['Content-Type'] == 'application/json'

        def it_returns_empty_array_when_no_squirrels_exist(server):
            response = make_request('GET', '/squirrels')
            body = json.loads(response['body'])
            assert body == []

        def it_returns_array_with_single_squirrel(server):
            make_request('POST', '/squirrels', {'name': 'TestSquirrel', 'size': 'medium'})
            response = make_request('GET', '/squirrels')
            body = json.loads(response['body'])
            assert len(body) == 1
            assert body[0]['name'] == 'TestSquirrel'

        def it_returns_multiple_squirrels_in_order(server):
            make_request('POST', '/squirrels', {'name': 'First', 'size': 'small'})
            make_request('POST', '/squirrels', {'name': 'Second', 'size': 'medium'})
            make_request('POST', '/squirrels', {'name': 'Third', 'size': 'large'})
            response = make_request('GET', '/squirrels')
            body = json.loads(response['body'])
            assert len(body) == 3
            assert body[0]['name'] == 'First'
            assert body[1]['name'] == 'Second'

        def it_includes_id_field_in_squirrel_objects(server):
            make_request('POST', '/squirrels', {'name': 'IdTest', 'size': 'small'})
            response = make_request('GET', '/squirrels')
            body = json.loads(response['body'])
            assert 'id' in body[0]

        def it_reflects_database_state_accurately(server):
            make_request('POST', '/squirrels', {'name': 'DbTest1', 'size': 'tiny'})
            make_request('POST', '/squirrels', {'name': 'DbTest2', 'size': 'huge'})
            response = make_request('GET', '/squirrels')
            db_records = get_db_records()
            body = json.loads(response['body'])
            assert len(body) == len(db_records)

    def describe_GET_squirrels_retrieve():

        def it_returns_200_status_code_for_valid_id(server):
            make_request('POST', '/squirrels', {'name': 'Findme', 'size': 'small'})
            db_records = get_db_records()
            squirrel_id = db_records[0]['id']
            response = make_request('GET', f'/squirrels/{squirrel_id}')
            assert response['status_code'] == 200

        def it_returns_json_content_type_for_retrieve(server):
            make_request('POST', '/squirrels', {'name': 'JsonTest', 'size': 'medium'})
            db_records = get_db_records()
            squirrel_id = db_records[0]['id']
            response = make_request('GET', f'/squirrels/{squirrel_id}')
            assert response['headers']['Content-Type'] == 'application/json'

        def it_returns_correct_squirrel_object(server):
            make_request('POST', '/squirrels', {'name': 'SpecificSquirrel', 'size': 'large'})
            db_records = get_db_records()
            squirrel_id = db_records[0]['id']
            response = make_request('GET', f'/squirrels/{squirrel_id}')
            body = json.loads(response['body'])
            assert body['name'] == 'SpecificSquirrel'
            assert body['size'] == 'large'

        def it_returns_first_squirrel_when_multiple_exist(server):
            make_request('POST', '/squirrels', {'name': 'FirstOne', 'size': 'tiny'})
            make_request('POST', '/squirrels', {'name': 'SecondOne', 'size': 'huge'})
            db_records = get_db_records()
            first_id = db_records[0]['id']
            response = make_request('GET', f'/squirrels/{first_id}')
            body = json.loads(response['body'])
            assert body['name'] == 'FirstOne'

        def it_returns_second_squirrel_when_requested(server):
            make_request('POST', '/squirrels', {'name': 'First', 'size': 'small'})
            make_request('POST', '/squirrels', {'name': 'Second', 'size': 'medium'})
            db_records = get_db_records()
            second_id = db_records[1]['id']
            response = make_request('GET', f'/squirrels/{second_id}')
            body = json.loads(response['body'])
            assert body['name'] == 'Second'

        def it_matches_database_record_exactly(server):
            make_request('POST', '/squirrels', {'name': 'ExactMatch', 'size': 'gigantic'})
            db_records = get_db_records()
            squirrel_id = db_records[0]['id']
            response = make_request('GET', f'/squirrels/{squirrel_id}')
            body = json.loads(response['body'])
            db_record = db_records[0]
            assert body['id'] == db_record['id']
            assert body['name'] == db_record['name']

    def describe_POST_squirrels_create():

        def it_returns_201_status_code_for_creation(server):
            response = make_request('POST', '/squirrels', {'name': 'NewSquirrel', 'size': 'medium'})
            assert response['status_code'] == 201

        def it_creates_squirrel_in_database(server):
            make_request('POST', '/squirrels', {'name': 'PersistTest', 'size': 'small'})
            records = get_db_records()
            assert len(records) == 1
            assert records[0]['name'] == 'PersistTest'

        def it_assigns_id_to_created_squirrel(server):
            make_request('POST', '/squirrels', {'name': 'IdAssign', 'size': 'large'})
            records = get_db_records()
            assert 'id' in records[0]
            assert records[0]['id'] is not None

        def it_creates_multiple_squirrels_sequentially(server):
            make_request('POST', '/squirrels', {'name': 'Multi1', 'size': 'tiny'})
            make_request('POST', '/squirrels', {'name': 'Multi2', 'size': 'medium'})
            make_request('POST', '/squirrels', {'name': 'Multi3', 'size': 'huge'})
            records = get_db_records()
            assert len(records) == 3

        def it_preserves_name_with_special_characters(server):
            make_request('POST', '/squirrels', {'name': 'Special-Name_123!', 'size': 'small'})
            records = get_db_records()
            assert records[0]['name'] == 'Special-Name_123!'

        def it_preserves_size_field_exactly(server):
            make_request('POST', '/squirrels', {'name': 'SizeTest', 'size': 'extra-large'})
            records = get_db_records()
            assert records[0]['size'] == 'extra-large'

        def it_can_be_retrieved_after_creation(server):
            make_request('POST', '/squirrels', {'name': 'RetrieveAfter', 'size': 'medium'})
            records = get_db_records()
            created_id = records[0]['id']
            response = make_request('GET', f'/squirrels/{created_id}')
            assert response['status_code'] == 200
            body = json.loads(response['body'])
            assert body['name'] == 'RetrieveAfter'

        def it_appears_in_list_after_creation(server):
            make_request('POST', '/squirrels', {'name': 'ListTest', 'size': 'large'})
            response = make_request('GET', '/squirrels')
            body = json.loads(response['body'])
            assert len(body) == 1
            assert body[0]['name'] == 'ListTest'

    def describe_PUT_squirrels_update():

        def it_returns_204_status_code_for_successful_update(server):
            make_request('POST', '/squirrels', {'name': 'Original', 'size': 'small'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            response = make_request('PUT', f'/squirrels/{squirrel_id}', {'name': 'Updated', 'size': 'large'})
            assert response['status_code'] == 204

        def it_updates_name_in_database(server):
            make_request('POST', '/squirrels', {'name': 'OldName', 'size': 'medium'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('PUT', f'/squirrels/{squirrel_id}', {'name': 'NewName', 'size': 'medium'})
            updated_records = get_db_records()
            assert updated_records[0]['name'] == 'NewName'

        def it_updates_size_in_database(server):
            make_request('POST', '/squirrels', {'name': 'SizeUpdate', 'size': 'tiny'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('PUT', f'/squirrels/{squirrel_id}', {'name': 'SizeUpdate', 'size': 'gigantic'})
            updated_records = get_db_records()
            assert updated_records[0]['size'] == 'gigantic'

        def it_updates_both_name_and_size(server):
            make_request('POST', '/squirrels', {'name': 'Before', 'size': 'before-size'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('PUT', f'/squirrels/{squirrel_id}', {'name': 'After', 'size': 'after-size'})
            updated_records = get_db_records()
            assert updated_records[0]['name'] == 'After'
            assert updated_records[0]['size'] == 'after-size'

        def it_preserves_id_after_update(server):
            make_request('POST', '/squirrels', {'name': 'IdPreserve', 'size': 'small'})
            records = get_db_records()
            original_id = records[0]['id']
            make_request('PUT', f'/squirrels/{original_id}', {'name': 'Updated', 'size': 'large'})
            updated_records = get_db_records()
            assert updated_records[0]['id'] == original_id

        def it_updates_only_specified_squirrel(server):
            make_request('POST', '/squirrels', {'name': 'First', 'size': 'small'})
            make_request('POST', '/squirrels', {'name': 'Second', 'size': 'medium'})
            make_request('POST', '/squirrels', {'name': 'Third', 'size': 'large'})
            records = get_db_records()
            second_id = records[1]['id']
            make_request('PUT', f'/squirrels/{second_id}', {'name': 'SecondUpdated', 'size': 'updated'})
            updated_records = get_db_records()
            assert updated_records[0]['name'] == 'First'
            assert updated_records[1]['name'] == 'SecondUpdated'

        def it_reflects_update_in_retrieve_endpoint(server):
            make_request('POST', '/squirrels', {'name': 'BeforeRetrieve', 'size': 'old'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('PUT', f'/squirrels/{squirrel_id}', {'name': 'AfterRetrieve', 'size': 'new'})
            response = make_request('GET', f'/squirrels/{squirrel_id}')
            body = json.loads(response['body'])
            assert body['name'] == 'AfterRetrieve'

        def it_reflects_update_in_list_endpoint(server):
            make_request('POST', '/squirrels', {'name': 'ListBefore', 'size': 'before'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('PUT', f'/squirrels/{squirrel_id}', {'name': 'ListAfter', 'size': 'after'})
            response = make_request('GET', '/squirrels')
            body = json.loads(response['body'])
            assert body[0]['name'] == 'ListAfter'

    def describe_DELETE_squirrels_delete():

        def it_returns_204_status_code_for_successful_delete(server):
            make_request('POST', '/squirrels', {'name': 'ToDelete', 'size': 'small'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            response = make_request('DELETE', f'/squirrels/{squirrel_id}')
            assert response['status_code'] == 204

        def it_removes_squirrel_from_database(server):
            make_request('POST', '/squirrels', {'name': 'WillBeDeleted', 'size': 'medium'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('DELETE', f'/squirrels/{squirrel_id}')
            remaining_records = get_db_records()
            assert len(remaining_records) == 0

        def it_deletes_only_specified_squirrel(server):
            make_request('POST', '/squirrels', {'name': 'Keep1', 'size': 'small'})
            make_request('POST', '/squirrels', {'name': 'DeleteThis', 'size': 'medium'})
            make_request('POST', '/squirrels', {'name': 'Keep2', 'size': 'large'})
            records = get_db_records()
            delete_id = records[1]['id']
            make_request('DELETE', f'/squirrels/{delete_id}')
            remaining = get_db_records()
            assert len(remaining) == 2
            assert remaining[0]['name'] == 'Keep1'

        def it_cannot_retrieve_deleted_squirrel(server):
            make_request('POST', '/squirrels', {'name': 'WillBeGone', 'size': 'small'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('DELETE', f'/squirrels/{squirrel_id}')
            response = make_request('GET', f'/squirrels/{squirrel_id}')
            assert response['status_code'] == 404

        def it_removes_squirrel_from_list(server):
            make_request('POST', '/squirrels', {'name': 'NotInList', 'size': 'medium'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('DELETE', f'/squirrels/{squirrel_id}')
            response = make_request('GET', '/squirrels')
            body = json.loads(response['body'])
            assert len(body) == 0

        def it_allows_deleting_first_of_multiple_squirrels(server):
            make_request('POST', '/squirrels', {'name': 'DeleteFirst', 'size': 'small'})
            make_request('POST', '/squirrels', {'name': 'KeepSecond', 'size': 'medium'})
            records = get_db_records()
            first_id = records[0]['id']
            make_request('DELETE', f'/squirrels/{first_id}')
            remaining = get_db_records()
            assert len(remaining) == 1
            assert remaining[0]['name'] == 'KeepSecond'

        def it_allows_deleting_last_of_multiple_squirrels(server):
            make_request('POST', '/squirrels', {'name': 'KeepFirst', 'size': 'small'})
            make_request('POST', '/squirrels', {'name': 'DeleteLast', 'size': 'medium'})
            records = get_db_records()
            last_id = records[1]['id']
            make_request('DELETE', f'/squirrels/{last_id}')
            remaining = get_db_records()
            assert len(remaining) == 1
            assert remaining[0]['name'] == 'KeepFirst'

    def describe_404_error_conditions():

        def it_returns_404_for_nonexistent_squirrel_on_retrieve(server):
            response = make_request('GET', '/squirrels/999999')
            assert response['status_code'] == 404

        def it_returns_404_for_nonexistent_squirrel_on_update(server):
            response = make_request('PUT', '/squirrels/888888', {'name': 'NoExist', 'size': 'none'})
            assert response['status_code'] == 404

        def it_returns_404_for_nonexistent_squirrel_on_delete(server):
            response = make_request('DELETE', '/squirrels/777777')
            assert response['status_code'] == 404

        def it_returns_404_for_POST_with_id(server):
            response = make_request('POST', '/squirrels/123', {'name': 'Invalid', 'size': 'none'})
            assert response['status_code'] == 404

        def it_returns_404_for_GET_on_invalid_resource(server):
            response = make_request('GET', '/invalid_resource')
            assert response['status_code'] == 404

        def it_returns_404_for_POST_on_invalid_resource(server):
            response = make_request('POST', '/invalid_resource', {'data': 'test'})
            assert response['status_code'] == 404

        def it_returns_404_for_PUT_on_invalid_resource(server):
            response = make_request('PUT', '/invalid_resource/123', {'data': 'test'})
            assert response['status_code'] == 404

        def it_returns_404_for_DELETE_on_invalid_resource(server):
            response = make_request('DELETE', '/invalid_resource/123')
            assert response['status_code'] == 404

        def it_returns_404_for_PUT_without_id(server):
            response = make_request('PUT', '/squirrels', {'name': 'NoId', 'size': 'none'})
            assert response['status_code'] == 404

        def it_returns_404_for_DELETE_without_id(server):
            response = make_request('DELETE', '/squirrels')
            assert response['status_code'] == 404

        def it_returns_404_with_text_plain_content_type(server):
            response = make_request('GET', '/squirrels/999999')
            assert response['headers']['Content-Type'] == 'text/plain'

        def it_returns_404_not_found_message_in_body(server):
            response = make_request('GET', '/invalid_path')
            assert response['body'] == '404 Not Found'

        def it_returns_404_for_deleted_squirrel_retrieve(server):
            make_request('POST', '/squirrels', {'name': 'Temporary', 'size': 'small'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('DELETE', f'/squirrels/{squirrel_id}')
            response = make_request('GET', f'/squirrels/{squirrel_id}')
            assert response['status_code'] == 404

        def it_returns_404_for_deleted_squirrel_update(server):
            make_request('POST', '/squirrels', {'name': 'Gone', 'size': 'small'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('DELETE', f'/squirrels/{squirrel_id}')
            response = make_request('PUT', f'/squirrels/{squirrel_id}', {'name': 'Update', 'size': 'new'})
            assert response['status_code'] == 404

        def it_returns_404_for_deleted_squirrel_second_delete(server):
            make_request('POST', '/squirrels', {'name': 'AlreadyGone', 'size': 'small'})
            records = get_db_records()
            squirrel_id = records[0]['id']
            make_request('DELETE', f'/squirrels/{squirrel_id}')
            response = make_request('DELETE', f'/squirrels/{squirrel_id}')
            assert response['status_code'] == 404

        def it_returns_404_for_zero_id(server):
            response = make_request('GET', '/squirrels/0')
            assert response['status_code'] == 404

        def it_returns_404_for_negative_id(server):
            response = make_request('GET', '/squirrels/-1')
            assert response['status_code'] == 404

        def it_returns_404_for_GET_with_extra_path_segments(server):
            response = make_request('GET', '/squirrels/1/extra')
            assert response['status_code'] == 404
