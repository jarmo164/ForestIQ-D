# List of all API endpoints

## Authentication

* `POST /password-login ALL_PRIVILEGES` - Log in via username and password.
* `POST /token-refresh Requires_Privilege(TOKEN_REFRESH)` - Use refresh token to get new usual token.
* `POST /totp Requires_Privilege(TOTP)` - Log In via Google Authenticator code.
* `POST /change-my-password ALL_PRIVILEGES` - Change my own password.

## Admin

### Users

* `GET /admin/users Requires_Privilege(ADMIN)` - Get all users
* `POST /admin/users Requires_Privilege(ADMIN)` - Create user
* `DELETE /admin/users/:user Requires_Privilege(ADMIN)` - Delete user
* `POST /admin/users/:user Requires_Privilege(ADMIN)` - Modify user privileges

### User statistics

* `GET /admin/userstatistics/owner-status-change Requires_Privilege(ADMIN)` - Get owner status change statistics
* `GET /admin/userstatistics/prep-data Requires_Privilege(ADMIN)` - Get user statistics form pre-fill data

### Possible owner statuses

* `GET /owner-statuses Requires_Privilege(ADMIN)` - Get possible owner statuses
* `DELETE /owner-statuses/:id Requires_Privilege(ADMIN)` - Delete possible owner status
* `POST /owner-statuses Requires_Privilege(ADMIN)` - Modify possible owner status

### Admin workdesk

* `POST /admin-workdesk/assign Requires_Privilege(ADMIN)` - Mass (re)assign owners to user
* `GET /admin-workdesk/owners-search Requires_Privilege(ADMIN)` - Search for owners based on different criteria
* `GET /admin-workdesk/prepare Requires_Privilege(ADMIN)` - Get admin workdesk form pre-fill data

### Contract

* `GET /contract-starter` - Get minimum data to start off a contract
* `GET /contracts/:id Requires_Privilege(ADMIN)` - Get old contract data
* `GET /contracts/:id/pdf Requires_Privilege(ADMIN)` - Download contract PDF
* `POST /contracts Requires_Privilege(ADMIN)` - Save contract and generate link for PDF
* `DELETE /contracts/:id Requires_Privilege(ADMIN)` - Delete old contract
* `GET /contracts Requires_Privilege(ADMIN)` - List of old contracts
* `GET /contracts/suggestors/cadastre/:id Requires_Privilege(ADMIN)` - Find matching Cadastre ID's.
* `GET /contracts/cadastre-details/:id Requires_Privilege(ADMIN)` - Get cadastre details bt ID
* `GET /contracts/suggestors/owner/:id Requires_Privilege(ADMIN)` - Find matching Owner ID's (SSC/Reg.No).
* `GET /contracts/owner-details/:id Requires_Privilege(ADMIN)` - Get owner details by ID

## Evaluators workdesk

* `GET /owners-in-need-of-evaluation Requires_Privilege(EVALUATION)` - List of owners set for evaluation

## Application messages

* `DELETE /application-messages/:id ALL_PRIVILEGES` - Delete application message
* `WS /application-messages ALL_PRIVILEGES` - Application messages websocket

## Cadastre actions

### Cadastre labels

* `POST /cadastres/:id/labels/:label Requires_Privilege(ASSIGNED_OWNERS)` - Add label to cadastre
* `GET /cadastres/:id/labels Requires_Privilege(ASSIGNED_OWNERS)` - Get labels attached to cadastre
* `DELETE /cadastres/:id/labels/:label Requires_Privilege(ASSIGNED_OWNERS)` - Remove label from cadastre

### Cadastre public data

* `GET /cadastres/:id/notifications Requires_Privilege(ASSIGNED_OWNERS)` - Get public forest notifications for cadastre
* `GET /cadastres/:id/mkdata Requires_Privilege(ASSIGNED_OWNERS)` - Get public forest plan data for cadastre
* `GET /cadastres/:id/areas Requires_Privilege(ASSIGNED_OWNERS)` - Get areas for cadastre

## Owner actions

* `GET /owners Requires_Privilege(OWNER_PROFILE)` - Search for owners based of different criteria.
* `GET /owners/:id Requires_Privilege(ASSIGNED_OWNERS(*) or OWNER_PROFILE)` - Get owner.
* `POST /owners/:id Requires_Privilege(ASSIGNED_OWNERS(*) or OWNER_PROFILE)` - Change owner details.
* `GET /owner/:id/status Requires_Privilege(ASSIGNED_OWNERS(*) or OWNER_PROFILE)` - Get owners current status.
* `POST /owners/:id/change-status Requires_Privilege(ASSIGNED_OWNERS(*) or OWNER_PROFILE)` - Change owners status.
* `POST /owners/:id/mark-cadastres Requires_Privilege(ASSIGNED_OWNERS)` - Mark certain cadastres of owner as interesting.
* `POST /owners/:id/refresh-cadastres Requires_Privilege(ASSIGNED_OWNERS)` - Refreshed owner ownings via UusKinnistuRaamat.
* `POST /owners/:id/add Requires_Privilege(OWNER_PROFILE)` - Add new owner
* `POST /owners/:id/log Requires_Privilege(ASSIGNED_OWNERS)` - Add a new comment for owner.
* `GET /owners/:id/log Requires_Privilege(ASSIGNED_OWNERS)` - Get owners previous comments and other log entries.
* `POST /owner/:id/assignee Requires_Privilege(ADMIN)` - (Re)assign owner to someone.

## Other callers work related stuff

* `GET /my-work/next-owner Requires_Privilege(ASSIGNED_OWNERS)` - Get next owner assigned to me
* `GET /my-work Requires_Privilege(ASSIGNED_OWNERS)` - Get all owners assigned to me
* `GET /caller-workdesk-prep-data Requires_Privilege(ASSIGNED_OWNERS)` - Get callers workdesk form pre-fill data

## Reminders

* `POST /reminders Requires_Privilege(ASSIGNED_OWNERS or OWNER_PROFILE)` - Add reminder
* `DELETE /reminders/:id Requires_Privilege(ASSIGNED_OWNERS or OWNER_PROFILE)` - Delete reminder
* `GET /reminders Requires_Privilege(ASSIGNED_OWNERS or OWNER_PROFILE)` - Get my reminders

## Persons dump - Just bunch of contacts not related to other stuff

* `GET /persons-dump Requires_Privilege(PHONES)` - Get contacts in persons dump

## Other

* `GET /status ALL_PRIVILEGES` - Is backend up?


\* Entries matched with requires privilege ASSIGNED_OWNERS(*) mean that if you only have ASSIGNED_OWNERS profile, you can only access this endpoint if the owner is currently assigned to you.
