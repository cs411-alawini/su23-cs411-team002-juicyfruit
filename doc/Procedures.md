
Procedure that inserts a user into the database
```sql
DELIMITER //
CREATE PROCEDURE user_data(IN id VARCHAR(255), computerID INT, name_ VARCHAR(255), password_ VARCHAR(255))
BEGIN
  IF id IN (SELECT UserID FROM User_Information) THEN 
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: ID already exists in User_Information table';
  ELSE
    INSERT INTO User_Information VALUES (id, computerID, name_, password_);
  END IF;
END; //
```

Procedure to insert a user review on a game. We make sure they own that game first
```sql
DELIMITER //
CREATE PROCEDURE user_review(p_ReccID INT, p_GameID INT, p_UserID VARCHAR(255), p_UserRating INT, p_TimePlayed INT)
BEGIN
  DECLARE game VARCHAR(255);
  IF p_GameID NOT IN (SELECT g.GameID FROM Games_Owned g WHERE p_UserID = g.UserID) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Game is not owned';
  END IF;
  SELECT GameName INTO game FROM Games WHERE Games.GameID = p_GameID;
  INSERT INTO User_Recommended_Games VALUES(p_ReccID, p_GameID, p_UserID, game, p_UserRating, p_TimePlayed);
END;
//
```

Procedure to add a friend to a user and a user to a friend
```sql
DELIMITER //
CREATE PROCEDURE add_friend(IN user VARCHAR(255), friend VARCHAR(255))
BEGIN
  IF user IN (SELECT UserID FROM User_Information) AND friend IN (SELECT UserID FROM User_Information)THEN 
    INSERT INTO Friends VALUES (user, friend);
    INSERT INTO Friends VALUES (friend, user);
  ELSE
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: ID doesn’t exists in User_Information table';
  END IF;
END
//
DELIMITER ;
```

Procedure to insert a user's computer information
```sql
DELIMITER //
CREATE PROCEDURE add_comp(user VARCHAR(255), os VARCHAR(255))
BEGIN
  DECLARE compid VARCHAR(255);
  SELECT u.ComputerID INTO compid FROM User_Information u WHERE u.UserID = user;
  IF os = 'Mac' THEN 
    INSERT INTO Computer_Information VALUES (compid, false, false, true);
  ELSEIF os = 'Windows' THEN
    INSERT INTO Computer_Information VALUES (compid, true, false, false);
  ELSEIF os = 'Linux' THEN
    INSERT INTO Computer_Information VALUES (compid, false, true, false);
  END IF;
END
//
DELIMITER ;
```

Procedure to add a game that the user wants
```sql
DELIMITER //
CREATE PROCEDURE add_owned_game(user VARCHAR(255), game_id INT)
BEGIN
  IF user IN (SELECT UserID FROM User_Information) THEN 
    INSERT INTO Games_Owned VALUES (user, game_id);
  ELSE
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: ID doesn’t exists in User_Information table';
  END IF;
END
//
DELIMITER ;
```

Procedure that checks if a game matches the users computer specs. If it does it will be inserted into the Meets_Specs table.
```sql
DELIMITER //
CREATE PROCEDURE specs(user VARCHAR(255), game_id INT)
BEGIN
  DECLARE compID VARCHAR(255);
  DECLARE w_os BOOL;
  DECLARE m_os BOOL;
  DECLARE l_os BOOL;
  
  IF user NOT IN (SELECT UserID FROM User_Information) THEN 
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: ID doesn’t exist in User_Information table';
  END IF;
  SELECT u.ComputerID INTO compID
  FROM  User_Information u 
  WHERE u.UserID = user;
  
  SELECT PlatformWindows, PlatformMac, PlatformLinux INTO w_os, m_os, l_os
  FROM  Computer_Information u
  WHERE u.ComputerID = ComputerID;
  IF m_os = true AND (SELECT PlatformMac FROM Games WHERE game_id = GameID) = true THEN
    INSERT INTO Meets_Specs VALUES (compID, game_id, false, false, true);
  ELSEIF w_os = true AND (SELECT PlatformWindows FROM Games WHERE game_id = GameID) = true THEN
    INSERT INTO Meets_Specs VALUES (compID, game_id, true, false, false);
  ELSEIF l_os = true AND (SELECT PlatformLinux FROM Games WHERE game_id = GameID) = true THEN
    INSERT INTO Meets_Specs VALUES (compID, game_id, false, true, false);
  ELSE 
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Game is not compatible';
  END IF;
  
END
//
DELIMITER ;
```

Procedure that updates a user's password
```sql
DELIMITER //
CREATE PROCEDURE update_password(IN username varchar(255), old_password varchar(255), new_password varchar(255))
BEGIN
    IF (username, old_password) IN (SELECT UserID, Password FROM User_Information)THEN
        UPDATE User_Information
        SET Password = new_password
        WHERE UserID = username;
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: This account doesnt exist!';
    END IF;
END;  //
DELIMITER ;
```

Procedure that searches the games based on the genre filter 
```sql
DELIMITER //
CREATE PROCEDURE game_genre(_genre VARCHAR(255))
BEGIN
  SET @sql = CONCAT('SELECT GameName, ReleaseDate, MetacriticRating, Price FROM Games WHERE ', _genre, ' = true;');
  PREPARE stmt FROM @sql;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;
END;
//
DELIMITER ;
```

Our advanced procedure that uses two advanced queries. The first advanced query is used to get the gameID, GameName, and UserRating from games that a user's friend recommended, and a cursor is pointing towards that. The second advanced query gets the average score of a game from our reviews dataset. When opening the cursor, we compare the score our friends give vs the average score and if the friend's score is higher, we insert it to a table so this game can be recommended to the user. We also decided that if the friend scored it over 90, then it also deserves to be recommended to the user. 
```sql
DELIMITER //
CREATE PROCEDURE adv_SP(user VARCHAR(255))
BEGIN
  DECLARE var_game_id INT;
  DECLARE var_game_name VARCHAR(255);
  DECLARE var_rating INT;
  DECLARE var_price float;
  DECLARE avgScore DECIMAL(10,4);
  
  DECLARE done BOOLEAN DEFAULT FALSE;
  DECLARE friend_game CURSOR FOR ( SELECT ur.GameID, ur.GameName, ur.UserRating
                                  FROM Friends f JOIN User_Recommended_Games ur ON (f.FriendID = ur.UserID)
                                  WHERE f.UserID = user
                                  GROUP BY GameID, GameName, UserRating
                                  HAVING UserRating > 50
                                  );
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
  DROP TABLE IF EXISTS NewTable;
  CREATE TABLE NewTable(game_id INT, game_name VARCHAR(255), rating float, price float);
  
  OPEN friend_game;
    cloop: LOOP
    FETCH friend_game INTO var_game_id, var_game_name, var_rating;
    SET var_price = (SELECT Price FROM Games g WHERE g.GameID = var_game_id);
    SET avgScore = (SELECT CAST(AVG(reviewScore) AS DECIMAL (10,4))
                    FROM Games g NATURAL JOIN Reviews r
                    WHERE g.GameID = var_game_id
                    GROUP BY g.GameID);
    IF done THEN
      LEAVE cloop;
    END IF;
    
    IF CAST(var_rating AS DECIMAL (10,4))/100 > avgScore THEN
      INSERT INTO NewTable VALUES(var_game_id, var_game_name,CAST(var_rating AS DECIMAL (10,4))/100, var_price);
    ELSEIF CAST(var_rating AS DECIMAL (10,4))/100 > .90 THEN
      INSERT INTO NewTable VALUES(var_game_id, var_game_name,CAST(var_rating AS DECIMAL (10,4))/100, var_price);
    END IF;
    END LOOP cloop;
    
    SELECT *
    FROM NewTable
    ORDER BY game_name;
END;
//
DELIMITER ;
```

Procedure that searches game price 
```sql
DELIMITER //
CREATE PROCEDURE GetGamesWithPrice(price_ FLOAT)
BEGIN
  SELECT DISTINCT GameName, ReleaseDate, Price
  FROM Games	
  WHERE Price = price_
  ORDER BY GameName;
END; 
```

Procedure that deletes a user from database
```sql
DELIMITER //
CREATE PROCEDURE delete_user(IN user_id varchar(255))
BEGIN
IF user_id IN (SELECT UserId FROM User_Information)
THEN
DELETE FROM User_Information
WHERE  UserId = user_id;
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: This game is not in your list!';

 END IF;
END //
```

Procedure that executes advanced subquery 1. This gets the average score, gameName, and metacritic ratings of a game where the user can search for games above a certain average score.
```sql
// DELIMITER
CREATE PROCEDURE RevScoreQuery(desired_score_ FLOAT)
BEGIN
SELECT g.GameName, MetacriticRating , CAST(AVG(reviewScore) AS DECIMAL (10,2))AS AvgScore
FROM Games g JOIN Reviews r ON (g.GameId = r.GameId)
GROUP BY g.GameName, MetacriticRating
HAVING AvgScore > desired_score_
ORDER BY g.GameName
LIMIT 15;
END; //
```

Procedure for advanced subquery 2. This gets the name, price, average score, and single-player vs multiplayer status. It is a union between games where it is searching for single-player or multiplayer games with a certain price and score.
```sql
DELIMITER //
CREATE PROCEDURE UnionQuery(price_ FLOAT, desired_score_ FLOAT)
BEGIN
(SELECT g.GameName, g.Price, CAST(AVG(reviewScore) AS DECIMAL (10,2))AS AvgScore, CategorySinglePlayer, CategoryMultiPlayer
FROM Games g JOIN Reviews r ON (g.GameId = r.GameId)
WHERE  CategorySinglePlayer = 1 AND g.Price > price_
GROUP BY g.GameName, g.Price, CategorySinglePlayer, CategoryMultiPlayer
HAVING AvgScore > desired_score_)

UNION

(SELECT g.GameName, g.Price, CAST(AVG(reviewScore) AS DECIMAL (10,2))AS AvgScore, CategorySinglePlayer, CategoryMultiPlayer
FROM Games g JOIN Reviews r ON (g.GameId = r.GameId)
WHERE  CategoryMultiPlayer = 1 AND  g.Price  < price_
GROUP BY g.GameName, g.Price, CategorySinglePlayer, CategoryMultiPlayer
HAVING AvgScore > desired_score_)
ORDER BY GameName
LIMIT 15;
END; //
```

Procedure that updates a user rating. But we can also update TimePlayed
```sql
DELIMITER //
CREATE PROCEDURE update_data(IN game_name varchar(255), updated_rating INT)
BEGIN

    IF game_name IN (SELECT GameName FROM User_Recommended_Games)THEN
        UPDATE User_Recommended_Games
        SET UserRating = updated_rating
        WHERE GameName = game_name;
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: This game is not in your list!';
    END IF;
END //
DELIMITER ;
```
