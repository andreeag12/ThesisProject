from fastapi import APIRouter, HTTPException
import boto3

router = APIRouter()
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Users")

@router.get("/test")
def test_table():
    try:
        return {"status": table.table_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
