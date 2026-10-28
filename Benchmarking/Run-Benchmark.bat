@echo off
start "Agentic Fusion Benchmark" powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0Benchmark.ps1"
