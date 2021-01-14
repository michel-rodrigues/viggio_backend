# Viggio - Backend

Viggio was a project strongly based on cameo.com, a platform where you can buy a video directly from a celebrity - which in this project is referred to as Talent. The entire development context was designed to be an MVP, with all resource limitations and time restrictions inherent to this type of project, taking 5 months to complete. This project also served as a sandbox for me to apply some concepts of Architecture Patterns and Design Patterns.

The backend is an HTTP REST API developed in Python with the Django framework and was provisioned on Google Cloud using Kubernetes. The entire flow of requesting and paying for a video by a user and uploading the video for a Talent (celebrity) uses the concepts Message Bus, Command Handler, and Ports & Adapters, to create abstraction layers. This structure can be found in the `viggio-backend/app/request_shoutout/` directory. There is also an abstraction layer in the email notification service for users and talents, making it possible to change the email service without having to change the domain, the code can be found at `viggio-backend/app/request_shoutout/domain/emails/` and `viggio-backend/app/post_office/`.
After uploading the video, to optimize the use of the storage service, a video transcode service was created to optimize the file size and include a watermark with the Viggio logo (`viggio-backend/app/transcoder/`).
The payment module implementation has been approved by the payment gateway provider companies and due to the abstraction layers in the video purchase and delivery flow, it was also possible to abstract much of the payment gateway implementation details, reducing the development effort in case it was necessary to change or add another payment gateway provider in the future.
The payment module, the video transcode service and the email notification were designed to run asynchronously using Celery. System faults are sent to Sentry and faults considered serious are sent to a group on Telegram.
There is a command to generate a CSV file with the amounts to be paid for the Talents in the month provided and a command to read a CSV file to update the status of payments made to the Talents.

The development environment was compartmentalized using Docker Compose and the deployment flow was automated in the GitOps style with Cloud Build, with load tests for configuring machine sizing and autoscale.

[*This repository is a copy of the private repository because some sensitive information was commited before being extracted to environment variables and configuration files*]
