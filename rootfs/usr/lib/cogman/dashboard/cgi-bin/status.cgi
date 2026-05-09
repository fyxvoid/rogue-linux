#!/bin/sh
printf 'Content-Type: text/plain\r\n'
printf 'Access-Control-Allow-Origin: *\r\n'
printf '\r\n'
cogman-ctl list 2>/dev/null || echo "supervisor not running"
