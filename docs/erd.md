

# Socket Chat — Database ERD



## 1. Overview



The database uses SQLite and contains four tables:

- `users`: stores user accounts.

- `rooms`: stores chat rooms.

- `room_members`: stores room membership.

- `messages`: stores private and room messages.



## 2. Entity Relationship Diagram



```mermaid

erDiagram

&#x20;   USERS ||--o{ MESSAGES : sends

&#x20;   USERS ||--o{ MESSAGES : receives

&#x20;   USERS ||--o{ ROOMS : creates

&#x20;   USERS ||--o{ ROOM_MEMBERS : joins

&#x20;   ROOMS ||--o{ ROOM_MEMBERS : contains

&#x20;   ROOMS ||--o{ MESSAGES : has



&#x20;   USERS {

&#x20;       INTEGER user_id PK

&#x20;       TEXT username UK

&#x20;       TEXT display_name

&#x20;       TEXT password_hash

&#x20;       TEXT created_at

&#x20;   }



&#x20;   ROOMS {

&#x20;       INTEGER room_id PK

&#x20;       TEXT name

&#x20;       INTEGER created_by FK

&#x20;       TEXT created_at

&#x20;   }



&#x20;   ROOM_MEMBERS {

&#x20;       INTEGER room_id PK, FK

&#x20;       INTEGER user_id PK, FK

&#x20;       TEXT joined_at

&#x20;   }



&#x20;   MESSAGES {

&#x20;       INTEGER message_id PK

&#x20;       INTEGER sender_id FK

&#x20;       INTEGER receiver_id FK

&#x20;       INTEGER room_id FK

&#x20;       TEXT content

&#x20;       TEXT sent_at

&#x20;   }

```



## 3. Relationships



- One user can send many messages.

- One user can receive many private messages.

- One user can create many chat rooms.

- Users can join multiple rooms, and each room can contain multiple users. The `room_members` table represents this many-to-many relationship.

- One room can contain many messages.



## 4. Message Types



The `messages` table supports two types of messages:



- **Private message:** `receiver_id` is populated and `room_id` is NULL.

- **Room message:** `room_id` is populated and `receiver_id` is NULL.



The database CHECK constraint requires exactly one of these two cases.



## 5. Notes



- `PK` means Primary Key.

- `FK` means Foreign Key.

- `UK` means Unique Key.

- The diagram describes the logical database structure, not a PCB or network architecture.




## 6. Display names

- `user_id` remains the unique identity and foreign-key target.
- `username` remains unique and is used for login. `display_name` may be shared by different users.
- Run `python -m database.init_db` before using the new code with an existing database. The migration backfills existing accounts with their username and preserves IDs, passwords and messages.
- `register_user(username, password, display_name=None)` returns the user ID as before. Omitting the display name defaults to the username.
- `get_user_profile(user_id)` returns a dictionary with user_id, username and display_name (or None).
- Pass `include_display_name=True` to `get_room_members` and `get_room_history` to append display_name to existing result tuples. Default calls retain the old tuple layout. The client should display display_name but select users and route messages by user_id (or unique username when required by the protocol).
