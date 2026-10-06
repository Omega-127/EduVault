import io
from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient, admin_auth_headers: dict):
    file_content = b"echo 'bad script'"
    files = {"file": ("malicious.exe", io.BytesIO(file_content), "application/x-msdownload")}

    response = await client.post(
        "/api/v1/documents/upload",
        headers=admin_auth_headers,
        files=files,
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_forbidden_for_student(client: AsyncClient, student_auth_headers: dict):
    files = {"file": ("regulations.pdf", io.BytesIO(b"%PDF-sample"), "application/pdf")}

    response = await client.post(
        "/api/v1/documents/upload",
        headers=student_auth_headers,
        files=files,
    )
    assert response.status_code == 403
    assert "Admin role required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_success_and_status(client: AsyncClient, admin_auth_headers: dict):
    sample_pdf = b"%PDF-1.4 ... Institutional Regulations ..."
    files = {"file": ("regulations.pdf", io.BytesIO(sample_pdf), "application/pdf")}

    with patch("app.storage.object_store.object_store.put", return_value="raw/test/regulations.pdf"), \
         patch("app.storage.object_store.object_store.ensure_bucket_exists"), \
         patch("app.ingestion.tasks.ingest_document.delay", return_value=MagicMock()):

        response = await client.post(
            "/api/v1/documents/upload",
            headers=admin_auth_headers,
            files=files,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["file_name"] == "regulations.pdf"
        assert data["status"] == "pending"
        doc_id = data["id"]

        # Check status endpoint
        status_res = await client.get(
            f"/api/v1/documents/{doc_id}/status",
            headers=admin_auth_headers,
        )
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "pending"
        assert status_res.json()["chunk_count"] == 0

        # Check list endpoint
        list_res = await client.get(
            "/api/v1/documents/",
            headers=admin_auth_headers,
        )
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_delete_document_success(client: AsyncClient, admin_auth_headers: dict):
    sample_txt = b"Campus Library Hours: Monday to Friday 8am to 10pm"
    files = {"file": ("library.txt", io.BytesIO(sample_txt), "text/plain")}

    with patch("app.storage.object_store.object_store.put", return_value="raw/test/library.txt"), \
         patch("app.storage.object_store.object_store.ensure_bucket_exists"), \
         patch("app.storage.object_store.object_store.delete", return_value=True), \
         patch("app.storage.vector_store.vector_store.delete_by_document_id"), \
         patch("app.ingestion.tasks.ingest_document.delay"):

        create_res = await client.post(
            "/api/v1/documents/upload",
            headers=admin_auth_headers,
            files=files,
        )
        doc_id = create_res.json()["id"]

        del_res = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers=admin_auth_headers,
        )
        assert del_res.status_code == 204

        # Verify it no longer exists
        get_res = await client.get(
            f"/api/v1/documents/{doc_id}",
            headers=admin_auth_headers,
        )
        assert get_res.status_code == 404
