@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Load values from .env
FOR /F "tokens=* delims=" %%i IN ('type .env') DO (
    SET "line=%%i"
    FOR /F "tokens=1,2 delims==" %%a IN ("!line!") DO (
        SET "%%a=%%b"
    )
)

REM Create the base64 encoded header
echo|set /p=%COMPANY_ID%+%PUBLIC_API_KEY%:%PRIVATE_API_KEY% > temp.txt
FOR /F %%i IN ('openssl base64 -in temp.txt') DO SET ENCODED_AUTH_STRING=%%i
del temp.txt

REM Ask user for the phone number
SET /P PHONE_NUMBER=Enter the phone number to search for: 

REM Construct and execute the curl command
curl -X GET ^
     -H "Authorization: Basic !ENCODED_AUTH_STRING!" ^
     -H "clientId: !CLIENT_ID!" ^
     "https://services.cns4u.com/v4_6_release/apis/3.0/company/companies?conditions=phoneNumber%20like%20'!PHONE_NUMBER!'"

ENDLOCAL
