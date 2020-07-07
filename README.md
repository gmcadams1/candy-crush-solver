# Candy Crush Solver

Implements a text-based Candy Crush game simulator using the "standard" 6-color candies and some of the "special" candies (striped candy and chocolate bombs).  Includes both the "normal" game mode that aims to just maximize score in a given number of moves, a "jelly" mode in which the player must destroy all jelly while obtaining a minimum score, and a "combined" game mode in which the player must destroy the jelly in a number of moves while also maximizing score.

Program includes a "random" player that selects a valid move at random, a "smart" player which implements the proposed algorithm, and a "human" player which prompts an interactive text-based Candy Crush game.

This was my successful submission as a prerequsite to receiving my Master's degree.

_Note_: Code needs cleaning up / optimization / more configurable main / etc.

## Logic
See pdf for details.

## Running
To run:
```
python <# games> <# moves per game> <# rows> <# cols>
```
### Additional inputs:
Run using a player implementing the proposed algorithm
```
Is player smart?(y or n)y
Enter max tree depth:5
Enter beam width:10
Starting Run #1
...
```
Run using a player who chooses moves randomly
```
Is player smart?(y or n)n
Starting Run #1
...
```
