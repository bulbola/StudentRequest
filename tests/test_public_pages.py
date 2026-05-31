def test_index_page_is_available(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "StudentRequest" in response.get_data(as_text=True)


def test_login_page_is_available(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Вход" in response.get_data(as_text=True)


def test_help_page_is_available(client):
    response = client.get("/help")
    assert response.status_code == 200
    assert "Справка" in response.get_data(as_text=True)