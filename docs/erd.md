

\# Socket Chat — Database ERD



\## 1. Overview



The database uses SQLite and contains four tables:

\- `users`: stores user accounts.

\- `rooms`: stores chat rooms.

\- `room\_members`: stores room membership.

\- `messages`: stores private and room messages.



\## 2. Entity Relationship Diagram



```mermaid

erDiagram

&#x20;   USERS ||--o{ MESSAGES : sends

&#x20;   USERS ||--o{ MESSAGES : receives

&#x20;   USERS ||--o{ ROOMS : creates

&#x20;   USERS ||--o{ ROOM\_MEMBERS : joins

&#x20;   ROOMS ||--o{ ROOM\_MEMBERS : contains

&#x20;   ROOMS ||--o{ MESSAGES : has



&#x20;   USERS {

&#x20;       INTEGER user\_id PK

&#x20;       TEXT username UK

&#x20;       TEXT password\_hash

&#x20;       TEXT created\_at

&#x20;   }



&#x20;   ROOMS {

&#x20;       INTEGER room\_id PK

&#x20;       TEXT name

&#x20;       INTEGER created\_by FK

&#x20;       TEXT created\_at

&#x20;   }



&#x20;   ROOM\_MEMBERS {

&#x20;       INTEGER room\_id PK, FK

&#x20;       INTEGER user\_id PK, FK

&#x20;       TEXT joined\_at

&#x20;   }



&#x20;   MESSAGES {

&#x20;       INTEGER message\_id PK

&#x20;       INTEGER sender\_id FK

&#x20;       INTEGER receiver\_id FK

&#x20;       INTEGER room\_id FK

&#x20;       TEXT content

&#x20;       TEXT sent\_at

&#x20;   }

```



\## 3. Relationships



\- One user can send many messages.

\- One user can receive many private messages.

\- One user can create many chat rooms.

\- Users can join multiple rooms, and each room can contain multiple users. The `room\_members` table represents this many-to-many relationship.

\- One room can contain many messages.



\## 4. Message Types



The `messages` table supports two types of messages:



\- \*\*Private message:\*\* `receiver\_id` is populated and `room\_id` is NULL.

\- \*\*Room message:\*\* `room\_id` is populated and `receiver\_id` is NULL.



The database CHECK constraint requires exactly one of these two cases.



\## 5. Notes



\- `PK` means Primary Key.

\- `FK` means Foreign Key.

\- `UK` means Unique Key.

\- The diagram describes the logical database structure, not a PCB or network architecture.



