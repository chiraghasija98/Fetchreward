#!/bin/bash
awslocal sqs create-queue --queue-name user-logins-queue
awslocal sqs send-message-batch --queue-url http://localhost:4566/000000000000/user-logins-queue --entries file://messages.json
