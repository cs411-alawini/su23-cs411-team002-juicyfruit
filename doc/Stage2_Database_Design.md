## Diagram:
<img src="./Diagram.png"> 

## Assumptions:

## Relational Schema/Logical Design: 

```sql
Games(
    gameID: INT [PK],
    gameName: varchar(255),
    genre: varchar(255),
    category: varchar(255),
    price: INT,
    minSpecs: varchar(255),
    recSpecs: varchar(255),
    numPlayers: INT,
    metaCriticRating: INT,
    numReccomendations: INT;
  );

  Reviews(
    reviewID: INT [PK],
    gameID: INT [PK],,
    GameName: varchar(255),
    reviewText: varchar(255),
    reviewVotes: INT
  );

User_Recommended_Games(
  LikedID: varchar(255) PRIMARY KEY,
  GameID: varchar(255) PRIMARY KEY,
  UserID: varchar(255) PRIMARY KEY,
  GameName: varchar(255),
  UserRating: INT,
  TimePlayed: INT;
);

User_Information(
  UserId: INT [PK],
  Name: VARCHAR(255),
  Password: VARCHAR(255),
  ComputerId: VARCHAR(255)
);

Computer_Information(
  ComputerId: VARCHAR(255) [PK],
  CPU: VARCHAR(255),
  GPU: VARCHAR(255),
  RAM: VARCHAR(10),
  Operating_sys: VARCHAR(255)
);

User_PC(
  UserId: INT [PK],
  ComputerId: VARCHAR(255) [PK]
);

Friends(
  UserId: INT [PK]
  FriendId: INT
);

Games_Owned( UserID: INT [PK],
  GameID: INT [PK] 
);

Meets_Specs( ComputerID: INT [PK],
	           GameID: INT [PK],
		MeetsMinSpec: BOOL,
		MeetsRecSpec: BOOL 
);

```
