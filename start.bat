@echo off
title Hostel 360 - Smart Hostel & Mess Management System
color 0A

echo ======================================================================
echo    HOSTEL 360: SMART HOSTEL & MESS MANAGEMENT SYSTEM
echo    SRM University Delhi-NCR, Sonepat - Department of CSE
echo    B.Tech CSE 7th Semester Live Project
echo    Authors: Dhruv Bansal, Arnav Ambasta, Janak Vallecha
echo ======================================================================
echo.

set AGY_NODE="C:\Users\DHRUV BANSAL\AppData\Roaming\Antigravity\bin\agy-node.cmd"
if not exist %AGY_NODE% (
    set AGY_NODE=node
)

echo [*] Starting Hostel 360 Live Server on http://localhost:3000 ...
start "" http://localhost:3000

call %AGY_NODE% "%~dp0backend_node\server.js"

pause
