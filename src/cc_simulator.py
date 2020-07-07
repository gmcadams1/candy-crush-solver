"""
    Filename: cc_simulator.py
    Author: Gregory McAdams
    E-mail: gmcadams1@comcast.net
"""
import random
import abc
import time
import copy
import math

def avg_row(anode):
    gb = anode.obj
    lm = gb.last_move

    if lm[2] == GameBoard.MOVES[0]:
        return int(lm[0]-1)
    elif lm[2] == GameBoard.MOVES[1]:
        return int(lm[0]+1)
    elif lm[2] == GameBoard.MOVES[2] or lm[2] == GameBoard.MOVES[3]:
        return int(lm[0])

class Driver:
    TYPE = ["human", "random", "ai"]

    def __init__(self, seed):
        self.gameBoards = []
        self.players = []
        random.seed(seed)

    # Create new GameBoard
    def append_game(self, rows, cols, mode):
        self.gameBoards.append(GameBoard(rows, cols, mode))

    # Create new Player
    def append_player(self, playerType, depth_limit=None, beam_width=None):
        if playerType == Driver.TYPE[0]:
            self.players.append(HumanPlayer())
        elif playerType == Driver.TYPE[1]:
            self.players.append(RandomPlayer())
        elif playerType == Driver.TYPE[2]:
            self.players.append(AIPlayer(depth_limit,beam_width))
        else:
            print("Shtop it")
            raise Exception("Shtop it")
    
    # Assign a GameBoard to a Player and then Player starts
    # Goal value corresponds to the value which when reached ends the game; depends on game mode
    def play_game(self, game_index, player_index, goal_value):
        self.players[player_index].init_board(self.gameBoards[game_index])
        self.players[player_index].start(goal_value)

class Player(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.gameBoard = None   # Player is assigned its GameBoard

    def init_board(self, game_board):
        self.gameBoard = game_board

    # Begin game
    def start(self, goal_value):
        if self.gameBoard == None:
            print("No assigned GameBoard, cannot start")
            raise Exception("No assigned GameBoard, cannot start")

        # Init/populate GameBoard
        self.gameBoard.start(goal_value)
        #self.gameBoard.print_board()

        # While we are not finished
        while self.gameBoard.finish == False:
            #print()
            #self.gameBoard.print_board()
            self.next_move()

        # Get info after game is finished
        #self.gameBoard.print_board()
        self.gameBoard.print_info()

    @abc.abstractmethod
    def next_move(self):
        return

class HumanPlayer(Player):
    def __init__(self):
        super().__init__()
        
    # Prompt user to make next move
    def next_move(self):
        while True:
            try:
                # Print board for human to see
                self.gameBoard.print_board()
                user_input = input("Enter as 'x,y,dir' or 'shuffle': ")
                if user_input == "shuffle":
                    self.gameBoard.shuffle()
                    continue
                user_input = user_input.split(",")
                self.gameBoard.move(int(user_input[0]),int(user_input[1]),user_input[2])
                break
            except RuntimeError as e:
                print("Exception: "+str(e))

class AIPlayer(Player):
    def __init__(self, depth_limit, beam_width):
        super().__init__()
        self.depth_limit = depth_limit
        self.beam_width = beam_width    # Percentage of top nodes to expand
        self.gameTree = None
        self.best_node = None  # Best pick for next move
        self.stored_states = {}   # Hash to store all previously seen states
        self.hash_hits = 0
        self.num_children = 0
        self.max_score = 0

        #print("Starting AI (depth_limit,beam_width): "+str(depth_limit)+","+str(beam_width))
    
    def init_tree(self):
        self.gameTree = Node(self.gameBoard,0)
    
    # Smart AI Player
    def next_move(self):
        # Get current game board
        self.init_tree()

        #print("Current Board: ")
        #self.gameTree.obj.print_board()

        # Reset best node
        self.best_node = None
        self.max_score = 0

        # Generate and build our game tree
        full_node_list = [self.gameTree]
        curr_node_list = [self.gameTree]
        curr_level = 0
        beam_width = self.beam_width
        while curr_level <= self.depth_limit and len(curr_node_list) > 0:
            children = []
            if curr_level == self.depth_limit:
                full_node_list.extend(curr_node_list)
                break
            for i in range(len(curr_node_list)):
                self.generate_levels(curr_node_list[i], curr_level, beam_width)
                children.extend(curr_node_list[i].children)
                full_node_list.append(curr_node_list[i])
            curr_node_list = []
            curr_node_list.extend(children)
            beam_width = int(math.sqrt(beam_width))
            curr_level = curr_level + 1

        # Go from bottom-up to find average scores
        for i in range(len(full_node_list)-1,-1,-1):
            full_node_list[i].find_avg_score()

        self.num_children = self.num_children + len(self.gameTree.children)

        # Take path with highest average heuristic cost
        for i in self.gameTree.children:
            #print("A child")
            #i.obj.print_board()
            #print("Last move: "+str(i.obj.last_move))
            #print("Score: "+str(i.score))
            if self.best_node == None:
                self.best_node = i
            elif i.score >= self.best_node.score:
                self.best_node = i

        #print("Best node last move is: "+str(self.best_node.obj.last_move))
        #print("Best node score is: "+str(self.best_node.obj.score))
        #print("Max score: "+str(self.max_score))

        next_move = self.best_node.obj.last_move
        self.gameBoard.move(next_move[0],next_move[1],next_move[2])
        #print("Current score: "+str(self.gameBoard.score))
        #print("Did move #: "+str(self.gameBoard.move_counter))

    def generate_levels(self, node, level, beam_width):
        children = []   # Potential children of this node
        use_hashing = False

        if node.obj.move_counter >= node.obj.goal_value["moves"]:
            if node.obj.score > self.max_score:
                self.max_score = node.obj.score
            return

        # Continue until we have at least one valid move
        while len(children) == 0:
            if use_hashing == True and node.obj.hash_key() in self.stored_states:
                children = self.stored_states[node.obj.hash_key()]
                self.hash_hits = self.hash_hits + 1
                break
            # Create the next level of tree
            for row in range(node.obj.rows):
                for col in range(node.obj.cols):
                    # For each candy, move right and down
                    try:
                        new_board = node.obj.copyme()
                        new_board.move(row,col,GameBoard.MOVES[3])
                        children.append(Node(new_board,self.h_func(node.obj,new_board,level+1),level+1))
                    except RuntimeError as e:
                        pass
                        #print("Exception: "+str(e))
                    try:
                        new_board = node.obj.copyme()
                        new_board.move(row,col,GameBoard.MOVES[1])
                        children.append(Node(new_board,self.h_func(node.obj,new_board,level+1),level+1))
                    except RuntimeError as e:
                        pass
                        #print("Exception: "+str(e))
            # No valid moves, we must shuffle
            if len(children) == 0:
                node.obj.shuffle()

        # First sort by average position in the board
        children.sort(key=avg_row, reverse=True)
        # Sort children on score, keep top % indicated by beam width
        children.sort(key=lambda child: child.score, reverse=True)

        if use_hashing == True and node.obj.hash_key() not in self.stored_states:
            # Add new state to hash
            self.stored_states[node.obj.hash_key()] = children

        #print("# Children(generate_levels): "+str(len(children)))
        final_children = children[:beam_width]
        #print("# Final Children(generate_levels): "+str(len(children)))
        node.add_children(final_children)
        #print("# Children Node: "+str(len(node.children)))

    def h_func_simple(self, parent_state, child_state, level):
        return (child_state.score/child_state.move_counter)

    # Determines the heuristic goodness score for a subsequent game board state
    def h_func(self, parent_state, child_state, level):
        score_diff = child_state.score - parent_state.score
        pair_striped = 0
        pair_choco = 0
        choco_nearby = {} # Ex. {Chocolate:[Candy,StripedCandy,Chocolate,...,]}
        candy_nearby = 0    # Counts identical color candy nearby
        color_count = {} # Ex. {'G':1,'R':2}
        striped_dict = {} # Ex. {'G':1,'R':0}
        h_val = 0

        # If this is the last move, just look at max score
        if child_state.move_counter >= child_state.goal_value["moves"]:
            return child_state.score

        for i in Candy.COLORS:
            color_count[i] = 0
 
        for row in range(len(self.gameBoard.squares)):
            for col in range(len(self.gameBoard.squares[row])):
                candy = child_state.squares[row][col].candy
                if isinstance(candy, Chocolate):
                    if candy not in choco_nearby:
                        choco_nearby[candy] = []
                    try:
                        candy_right = child_state.squares[row][col+1].candy
                        if isinstance(candy_right, Chocolate):
                            pair_choco = pair_choco + 1
                            # Avoid double counting
                            choco_nearby[candy] = None
                            choco_nearby[candy_right] = None
                        elif isinstance(candy_right, Candy):
                            if choco_nearby[candy] != None:
                                choco_nearby[candy].append(candy_right)
                    except IndexError as e:
                        pass
                    try:
                        candy_down = child_state.squares[row+1][col].candy
                        if isinstance(candy_down, Chocolate):
                            pair_choco = pair_choco + 1
                            # Avoid double counting
                            choco_nearby[candy] = None
                            choco_nearby[candy_down] = None
                        elif isinstance(candy_down, Candy):
                            if choco_nearby[candy] != None:
                                choco_nearby[candy].append(candy_down)
                    except IndexError as e:
                        pass
                elif isinstance(candy, StripedCandy):
                    color_count[candy.color] = color_count[candy.color] + 1
                    try:
                        candy_right = child_state.squares[row][col+1].candy
                        if isinstance(candy_right, Chocolate):
                            if candy_right not in choco_nearby:
                                choco_nearby[candy_right] = [candy]
                            elif choco_nearby[candy_right] != None:
                                choco_nearby[candy_right].append(candy)
                        elif isinstance(candy_right, StripedCandy):
                            pair_striped = pair_striped + 1
                        elif candy.color == candy_right.color:
                            if candy.direction == StripedCandy.DIR[0]:
                                # Striped candy next to a same colored candy is worth more
                                candy_nearby = candy_nearby + (child_state.rows/3.0)
                            else:
                                candy_nearby = candy_nearby + (child_state.cols/3.0)
                    except IndexError as e:
                        pass
                    try:
                        candy_down = child_state.squares[row+1][col].candy
                        if isinstance(candy_down, Chocolate):
                            if candy_down not in choco_nearby:
                                choco_nearby[candy_down] = [candy]
                            elif choco_nearby[candy_down] != None:
                                choco_nearby[candy_down].append(candy)
                        elif isinstance(candy_down, StripedCandy):
                            pair_striped = pair_striped + 1
                        elif candy.color == candy_down.color:
                            if candy.direction == StripedCandy.DIR[0]:
                                # Striped candy next to a same colored candy is worth more
                                candy_nearby = candy_nearby + (child_state.rows/3.0)
                            else:
                                candy_nearby = candy_nearby + (child_state.cols/3.0)
                    except IndexError as e:
                        pass
                else:
                    color_count[candy.color] = color_count[candy.color] + 1
                    try:
                        candy_right = child_state.squares[row][col+1].candy
                        if isinstance(candy_right, Chocolate):
                            if candy_right not in choco_nearby:
                                choco_nearby[candy_right] = [candy]
                            elif choco_nearby[candy_right] != None:
                                choco_nearby[candy_right].append(candy)
                        elif candy.color == candy_right.color:
                            if isinstance(candy_right, StripedCandy):
                                if candy_right.direction == StripedCandy.DIR[0]:
                                    # Striped candy next to a same colored candy is worth more
                                    candy_nearby = candy_nearby + (child_state.rows/3.0)
                                else:
                                    candy_nearby = candy_nearby + (child_state.cols/3.0)
                            else:
                                candy_nearby = candy_nearby + 1
                    except IndexError as e:
                        pass
                    try:
                        candy_down = child_state.squares[row+1][col].candy
                        if isinstance(candy_down, Chocolate):
                            if candy_down not in choco_nearby:
                                choco_nearby[candy_down] = [candy]
                            elif choco_nearby[candy_down] != None:
                                choco_nearby[candy_down].append(candy)
                        elif candy.color == candy_down.color:
                            if isinstance(candy_down, StripedCandy):
                                if candy_down.direction == StripedCandy.DIR[0]:
                                    # Striped candy next to a same colored candy is worth more
                                    candy_nearby = candy_nearby + (child_state.rows/3.0)
                                else:
                                    candy_nearby = candy_nearby + (child_state.cols/3.0)
                            else:
                                candy_nearby = candy_nearby + 1
                    except IndexError as e:
                        pass

        # Add in score for each paired striped candy
        h_val = h_val + (pair_striped*(child_state.rows+child_state.cols))

        # Add in score for each chocolate (unpaired)
        # Find greatest score
        for i in choco_nearby:
            if choco_nearby[i] == None:
                continue
            max_val = 0
            for j in choco_nearby[i]:
                if isinstance(j, StripedCandy):
                    temp = color_count[j.color]
                    val = 0
                    # Assign random directions to new striped candies
                    for k in range(temp):
                        sdir = random.choice(['up','down'])
                        if sdir == 'up':
                            val = val + child_state.rows
                        else:
                            val = val + child_state.cols
                    if val > max_val:
                        max_val = val
                else:
                    temp = color_count[j.color]
                    if temp > max_val:
                        max_val = temp
            # Add one for chocolate
            h_val = h_val + max_val + 1

        # Add in score for each paired chocolate
        h_val = h_val + (pair_choco*(child_state.rows*child_state.cols))

        # Add in score for candy color in proximity to one another
        h_val = h_val + candy_nearby

        #print("h_val: "+str(h_val))
        #print("score_diff: "+str(score_diff))
        #print("diff : "+str(parent_state.state_compare_diff(child_state)))

        # Difference in score between parent and child state
        h_val = h_val + (score_diff)

        #diff = parent_state.state_compare_diff(child_state)

        #if score_diff >= diff:
            #h_val = h_val * ((score_diff-diff)/len(Candy.COLORS))
        #else:
            #h_val = h_val * (1.0/((diff-score_diff)*len(Candy.COLORS)))

        #print("***Parent***")
        #parent_state.print_board()
        #print("Move: "+str(child_state.last_move))
        #print("***Child***")
        #print("pair_striped: "+str(pair_striped))
        #print("pair_choco: "+str(pair_choco))
        #print("candy_nearby: "+str(candy_nearby))
        #print("score_diff: "+str(score_diff))
        #print("h_val: "+str(h_val))
        #child_state.print_board()
        return h_val

class RandomPlayer(Player):
    def __init__(self):
        super().__init__()
    
    # Totally random Player
    def next_move(self):
        moves = []
        while True:
            if len(moves) == 0:
                for row in range(len(self.gameBoard.squares)):
                    for col in range(len(self.gameBoard.squares[row])):
                        moves.append((row,col,"r"))
                        moves.append((row,col,"d"))
            try:
                move_idx = random.randrange(len(moves))
                move = moves[move_idx]
                moves.pop(move_idx)
                self.gameBoard.move(move[0],move[1], move[2])
                break
            except RuntimeError as e:
                pass

            if len(moves) == 0:
                self.gameBoard.shuffle()

        #print("I moved "+str(movePos)+" in direction "+str(moveDir))

# Each node has an object and its heuristic score
class Node:
    def __init__(self, obj, score, level=None):
        self.obj = obj
        self.score = score
        if level == None:
            self.level = 0
        else:
            self.level = level
        self.children = []
        self.parent = None

    def add_child(self, obj, score):
        self.children.append(Node(obj,score))
        self.children[-1].parent = self

    def add_children(self, children):
        for child in children:
            child.parent = self
        self.children.extend(children)

    def find_avg_score(self):
        if len(self.children) > 0:
            children_score = 0
            for i in self.children:
                children_score = children_score + i.score
            avg_children = children_score/len(self.children)
            self.score = (self.score+avg_children)/2.0

    def delete(self):
        self.obj = None
        self.score = None
        for i in self.children:
            i.delete()

class GameBoard:
    MOVES = ["u", "d", "l", "r"]    # Up,down,left,right
    MODE = ["main", "time", "jelly", "main+jelly"]

    def __init__(self, rows, cols, mode):
        self.last_move = None   # ex. (row,col,"down")
        self.rows = rows
        self.cols = cols
        self.score = 0  # 1 point for each crush
        self.move_counter = 0
        self.start_time = None
        self.finish = False
        self.goal_value = None
        self.squares = [[0 for j in range(self.cols)] for i in range(self.rows)]
        if mode in GameBoard.MODE:
            self.mode = mode
        else:
            print("ERROR: Invalid Mode of Play")
            raise Exception("Invalid Mode of Play")

    def copyme(self):
        copyTo = GameBoard(self.rows,self.cols,self.mode)
        #copyTo.last_move = self.last_move
        copyTo.score = self.score
        copyTo.move_counter = self.move_counter
        copyTo.start_time = self.start_time
        copyTo.finish = self.finish
        copyTo.goal_value = self.goal_value

        for row in range(len(self.squares)):
            for col in range(len(self.squares[row])):
                copyTo.squares[row][col] = self.squares[row][col].copyme()

        if hasattr(self, 'active_jelly'):
            copyTo.active_jelly = self.active_jelly

        return copyTo

    def swap_candy(self, moveFromRow, moveFromCol, moveToRow, moveToCol):
        temp_candy = self.squares[moveFromRow][moveFromCol].candy
        self.squares[moveFromRow][moveFromCol].candy = self.squares[moveToRow][moveToCol].candy
        self.squares[moveToRow][moveToCol].candy = temp_candy

    def shuffle(self):
        old_score = self.score
        for row in range(len(self.squares)):
            for col in range(len(self.squares[row])):
                self.swap_candy(row,col,random.randrange(self.rows),random.randrange(self.cols))
        res = True
        while res == True:
            res = self.update_board()
        # Reset to old score in case a shuffle caused some crushes
        self.score = old_score

    # Create board and init variables
    # Used as a reset as well
    def start(self, goal_value):
        # Init each square in the game board
        for row in range(len(self.squares)):
            for col in range(len(self.squares[row])):
                self.squares[row][col] = Square()

        # Needed so that the initial board has no crushes when Player begins
        res = True
        while res == True:
            res = self.update_board()

        # If we are in jelly mode, randomly set some jelly
        if self.mode == GameBoard.MODE[2] or self.mode == GameBoard.MODE[3]:
            self.active_jelly = goal_value["jelly"]
            for i in range(self.active_jelly):
                while True:
                    try:
                        row = random.randrange(self.rows)
                        col = random.randrange(self.cols)
                        self.squares[row][col].set_jelly()
                        break
                    except RuntimeError as e:
                        pass

        # Set/reset variables
        self.move_counter = 0   # Move counter
        self.score = 0   # Reset
        self.start_time = time.time()   # Time elapsed (real time)
        self.finish = False   # True when goal reached
        self.goal_value = goal_value   # Goal value based on mode

    def move(self, moveRow, moveCol, moveDir):
        if not isinstance(moveRow,int) or not isinstance(moveCol,int):
            raise RuntimeError("Not a valid row or column")

        # Check to see if the move is a legal move #

        # Check for out-of-bounds, (Maybe: then check for valid move)
        if moveDir == GameBoard.MOVES[0]:
            if moveRow <= 0:
                raise RuntimeError("Cannot move up") 
            else:
                self.move_up(moveRow, moveCol)

        elif moveDir == GameBoard.MOVES[1]:
            if moveRow >= self.rows-1:
                raise RuntimeError("Cannot move down")
            else:
                self.move_down(moveRow, moveCol)

        elif moveDir == GameBoard.MOVES[2]:
            if moveCol <= 0:
                raise RuntimeError("Cannot move left")
            else:
                self.move_left(moveRow, moveCol)

        elif moveDir == GameBoard.MOVES[3]:
            if moveCol >= self.cols-1:
                raise RuntimeError("Cannot move right")
            else:
                self.move_right(moveRow, moveCol)

        else:
            print("Invalid direction")
            raise RuntimeError("Invalid direction")

        self.last_move = (moveRow, moveCol, moveDir)

        # Update the board
        res = True
        while res == True:
            res = self.update_board()

        # Increment move counter
        self.move_counter = self.move_counter + 1

        # Now see if goal has been reached #
        
        # Check if score or max moves are reached, if we are in main mode
        if self.mode == GameBoard.MODE[0]:
            if self.score >= self.goal_value["score"]:
                self.finish = True
            elif self.move_counter >= self.goal_value["moves"]:
                self.finish = True
            elif self.move_counter > self.goal_value["moves"]:
                raise Exception("ERROR: Max moves reached, but a move happened")
                print("ERROR: Max moves reached, but a move happened")
        # Check if time is up, if we are in time mode
        elif self.mode == GameBoard.MODE[1]:
            if time.time() - self.start_time >= self.goal_value["time"]:
                self.finish = True
        # Check if all jelly was eliminated, if in jelly mode
        elif self.mode == GameBoard.MODE[2]:
            if self.active_jelly == 0:
                self.finish = True
        # Check if score is reached and all jelly is eliminated, or if max moves is reached
        # Main mode + Jelly mode, mode
        elif self.mode == GameBoard.MODE[3]:
            if self.score >= self.goal_value["score"] and self.active_jelly == 0:
                self.finish = True
            elif self.move_counter == self.goal_value["moves"]:
                self.finish = True
            elif self.move_counter > self.goal_vlaue["moves"]:
                raise Exception("ERROR: Max moves reached, but a move happened")
                print("ERROR: Max moves reached, but a move happened")
        else:
            print("You shouldn't see this")
            raise Exception("You shouldn't see this")

    def move_up(self, moveRow, moveCol):
        # Need to check if either is a chocolate
        if isinstance(self.squares[moveRow][moveCol].candy, Chocolate) \
                    or isinstance(self.squares[moveRow-1][moveCol].candy, Chocolate):
            # First remove the 2 candies and add 2 points
            candy1 = self.squares[moveRow][moveCol].candy.copyme()
            candy2 = self.squares[moveRow-1][moveCol].candy.copyme()
            self.squares[moveRow][moveCol].candy = None
            self.squares[moveRow-1][moveCol].candy = None
            self.score = self.score + 2
            # Now check for which combo
            self.chocolate_combo(candy1, candy2)
        
        # Need to check if both are striped candies
        elif isinstance(self.squares[moveRow][moveCol].candy, StripedCandy) \
                    and isinstance(self.squares[moveRow-1][moveCol].candy, StripedCandy):
            self.squares[moveRow][moveCol].candy = None
            self.squares[moveRow-1][moveCol].candy = None
            self.stripe_combo(moveRow-1, moveCol)

        # Else, just a normal move
        else:
            # Make sure this move matches at least 3
            self.check_match(moveRow,moveCol,moveRow-1,moveCol)
            self.swap_candy(moveRow,moveCol,moveRow-1,moveCol)

    def move_down(self, moveRow, moveCol):
        # Need to check if either is a chocolate
        if isinstance(self.squares[moveRow][moveCol].candy, Chocolate) \
                    or isinstance(self.squares[moveRow+1][moveCol].candy, Chocolate):
            # First remove the 2 candies and add 2 points
            candy1 = self.squares[moveRow][moveCol].candy.copyme()
            candy2 = self.squares[moveRow+1][moveCol].candy.copyme()
            self.squares[moveRow][moveCol].candy = None
            self.squares[moveRow+1][moveCol].candy = None
            self.score = self.score + 2
            # Now check for which combo
            self.chocolate_combo(candy1, candy2)

        # Need to check if both are striped candies
        elif isinstance(self.squares[moveRow][moveCol].candy, StripedCandy) \
                    and isinstance(self.squares[moveRow+1][moveCol].candy, StripedCandy):
            self.squares[moveRow][moveCol].candy = None
            self.squares[moveRow+1][moveCol].candy = None
            self.stripe_combo(moveRow+1, moveCol)

        # Else, just a normal move
        else:
            # Make sure this move matches at least 3
            self.check_match(moveRow,moveCol,moveRow+1,moveCol)
            self.swap_candy(moveRow,moveCol,moveRow+1,moveCol)

    def move_left(self, moveRow, moveCol):
        # Need to check if either is a chocolate
        if isinstance(self.squares[moveRow][moveCol].candy, Chocolate) \
                    or isinstance(self.squares[moveRow][moveCol-1].candy, Chocolate):
            # First remove the 2 candies and add 2 points
            candy1 = self.squares[moveRow][moveCol].candy.copyme()
            candy2 = self.squares[moveRow][moveCol-1].candy.copyme()
            self.squares[moveRow][moveCol].candy = None
            self.squares[moveRow][moveCol-1].candy = None
            self.score = self.score + 2
            # Now check for which combo
            self.chocolate_combo(candy1, candy2)

        # Need to check if both are striped candies
        elif isinstance(self.squares[moveRow][moveCol].candy, StripedCandy) \
                    and isinstance(self.squares[moveRow][moveCol-1].candy, StripedCandy):
            self.squares[moveRow][moveCol].candy = None
            self.squares[moveRow][moveCol-1].candy = None
            self.stripe_combo(moveRow, moveCol-1)

        # Else, just a normal move
        else:
            # Make sure this move matches at least 3
            self.check_match(moveRow,moveCol,moveRow,moveCol-1)
            self.swap_candy(moveRow,moveCol,moveRow,moveCol-1)

    def move_right(self, moveRow, moveCol):
        # Need to check if either is a chocolate
        if isinstance(self.squares[moveRow][moveCol].candy, Chocolate) \
                    or isinstance(self.squares[moveRow][moveCol+1].candy, Chocolate):
            # First remove the 2 candies and add 2 points
            candy1 = self.squares[moveRow][moveCol].candy.copyme()
            candy2 = self.squares[moveRow][moveCol+1].candy.copyme()
            self.squares[moveRow][moveCol].candy = None
            self.squares[moveRow][moveCol+1].candy = None
            self.score = self.score + 2
            # Now check for which combo
            self.chocolate_combo(candy1, candy2)

        # Need to check if both are striped candies
        elif isinstance(self.squares[moveRow][moveCol].candy, StripedCandy) \
                    and isinstance(self.squares[moveRow][moveCol+1].candy, StripedCandy):
            self.squares[moveRow][moveCol].candy = None
            self.squares[moveRow][moveCol+1].candy = None
            self.stripe_combo(moveRow, moveCol+1)

        # Else, just a normal move
        else:
            # Make sure this move matches at least 3
            self.check_match(moveRow,moveCol,moveRow,moveCol+1)
            self.swap_candy(moveRow,moveCol,moveRow,moveCol+1)

    # Creates a copy of this game and does the move
    # If nothing is crushed, then the move is invalid
    def check_match(self, moveFromRow, moveFromCol, moveToRow, moveToCol):
        temp_board = self.copyme()
        temp_board.swap_candy(moveFromRow, moveFromCol, moveToRow, moveToCol)

        res = temp_board.check_valid_move()
        if res == False:
            raise RuntimeError("Not a valid 3-match move")

    def check_valid_move(self):
        for row in range(len(self.squares)):
            for col in range(len(self.squares[row])):
                # For each square, see if we have 3/4/5 matching colors
                # After a crush, we repopulate the empty squares and restart this
                
                # Check if we have a match to the right
                if col < self.cols-2:
                    res_right = self.check_right(row, col)
                    if res_right == True:
                        return True

                # Check if we have a match down
                if row < self.rows-2:
                    res_down = self.check_down(row, col)
                    if res_down == True:
                        return True

        # Nothing crushed
        return False

    # Chocolate + Candy
    def chocolate_combo(self, candy1, candy2):
        candy = None    # Copy of candy exchanged with chocolate

        # If both are chocolate, clear the entire board
        if isinstance(candy1, Chocolate) and isinstance(candy2, Chocolate):
            for row in range(len(self.squares)):
                for col in range(len(self.squares[row])):
                    if not isinstance(self.squares[row][col].candy, Chocolate):
                        self.squares[row][col].candy = None
                        self.squares[row][col].set_candy()
                        self.score = self.score + 1
                    else:
                        self.squares[row][col].candy.exploding = True
            return
        
        # Else if candy1 is a candy
        elif isinstance(candy2, Chocolate):
            candy = candy1.copyme()

        # Else if candy2 is candy
        elif isinstance(candy1, Chocolate):
            candy = candy2.copyme()

        else:
            print("No chocolates here: Candy1: "+str(candy1.color)+" Candy2: "+str(candy2.color))
            raise Exception("No chocolates here: Candy1: "+str(candy1.color)+" Candy2: "+str(candy2.color))

        # Chocolate + Striped Candy
        if isinstance(candy, StripedCandy):
            # Now turn every same candy into striped candy of random direction
            for row in range(len(self.squares)):
                for col in range(len(self.squares[row])):
                    if self.squares[row][col].candy != None and self.squares[row][col].candy.color == candy.color:
                        self.squares[row][col].candy = None
                        self.squares[row][col].set_striped_candy(candy.color)

        # Finally, crush all the candies of the same color one-by-one
        for row in range(len(self.squares)):
            for col in range(len(self.squares[row])):
                if self.squares[row][col].candy != None and self.squares[row][col].candy.color == candy.color:
                    self.crush_candy(row,col,row,col)

        self.move_and_refill()

    # Striped Candy + Striped Candy
    def stripe_combo(self, moveRow, moveCol):
        # First crush all candies in the same column
        self.crush_candy(0,moveCol,self.rows-1,moveCol)

        # Then crush all candies in the same row
        self.crush_candy(moveRow,0,moveRow,self.cols-1)

        self.move_and_refill()

    # Crush all candy from one square to another in some direction
    def crush_candy(self, crushFromRow, crushFromCol, crushToRow, crushToCol):
        #self.print_board()
        #print("Crush from,to: "+str(crushFromRow)+","+str(crushFromCol)+" "+str(crushToRow)+","+str(crushToCol))
        for row in range(crushFromRow,crushToRow+1):
            for col in range(crushFromCol, crushToCol+1):
                # If no candy here, ignore
                if self.squares[row][col].candy == None:
                    continue
    
                # If jelly here, eliminate it
                if self.squares[row][col].jelly == True:
                    self.squares[row][col].jelly = False
                    self.active_jelly = self.active_jelly - 1

                # If this is a striped candy, recurse and crush more
                if isinstance(self.squares[row][col].candy,StripedCandy):
                    # If vertical striped candy
                    if self.squares[row][col].candy.direction == StripedCandy.DIR[0]:
                        self.squares[row][col].candy = None
                        self.score = self.score + 1
                        self.crush_candy(0,col,self.rows-1,col)
                    # Else, horizontal striped candy
                    else:
                        self.squares[row][col].candy = None
                        self.score = self.score + 1
                        self.crush_candy(row,0,row,self.cols-1)
                # If this is a chocolate, destroy all same random colored candy
                elif isinstance(self.squares[row][col].candy,Chocolate):
                    self.squares[row][col].candy = None
                    self.score = self.score + 1
                    acolor = Candy.COLORS[random.randrange(len(Candy.COLORS))]
                    for row in range(len(self.squares)):
                        for col in range(len(self.squares[row])):
                            if self.squares[row][col].candy != None \
                                        and self.squares[row][col].candy.color == acolor:
                                self.squares[row][col].candy = None
                                self.score = self.score + 1
                # Else, just a normal Candy
                else:
                    self.squares[row][col].candy = None
                    self.score = self.score + 1

    # Continue crushing until nothing else is crushable on the board
    # Go from top-down, left-right
    # Return True if there was a crush, False otherwise
    def update_board(self):
        for row in range(len(self.squares)):
            for col in range(len(self.squares[row])):
                # For each square, see if we have 3/4/5 matching colors
                # After a crush, we repopulate the empty squares and restart this
                
                # Check if we have a match to the right
                if col < self.cols-2:
                    res_right = self.check_right(row, col)

                # Check if we have a match down
                if row < self.rows-2 and res_right != True:
                    res_down = self.check_down(row, col)

                # Note: Redundant to also check up and left

                # If we have crushed at least something, move and refill the board
                # Return True so this process can go again with the refilled board
                if res_right == True or res_down == True:
                    self.move_and_refill()
                    return True

        # Nothing crushed
        return False

    # Check if we match 3 or more to the right, starting at (row,col)
    def check_right(self, row, col):
        col_pos = col
        candy = self.squares[row][col].candy

        # Chocolates never match 3+ with themselves
        if isinstance(candy, Chocolate):
            if candy.exploding == True:
                self.crush_candy(row,col,row,col)
                return True
            return
 
        match_counter = 0
        # Check right
        while col_pos < self.cols and match_counter <= 4:
            if candy.color == self.squares[row][col_pos].candy.color:
                match_counter = match_counter + 1
                col_pos = col_pos + 1
            else:
                break
        # If we matched at least 3 colors, we crush something
        if match_counter >= 3:
            self.crush_candy(row,col,row,col+match_counter-1)
            # Match 3; standard crush
            if match_counter == 3:
                pass
            # Match 4; striped candy formed after crush
            elif match_counter == 4:
                self.squares[row][col].set_striped_candy(candy.color,StripedCandy.DIR[0])
            # Match 5; chocolate formed after crush
            else:
                self.squares[row][col].set_chocolate()

            return True

    # Check if we match 3 or more down, starting at (row,col)
    def check_down(self, row, col):
        row_pos = row
        candy = self.squares[row][col].candy

        # Chocolates never match 3+ with themselves
        if isinstance(candy, Chocolate):
            if candy.exploding == True:
                self.crush_candy(row,col,row,col)
                return True
            return

        match_counter = 0
        # Check down
        while row_pos < self.rows and match_counter <= 4:
            if candy.color == self.squares[row_pos][col].candy.color:
                match_counter = match_counter + 1
                row_pos = row_pos + 1
            else:
                break

        # If we matched at least 3 colors, we crush something
        if match_counter >= 3:
            self.crush_candy(row,col,row+match_counter-1,col)
            # Match 3; standard crush
            if match_counter == 3:
                pass
            # Match 4; striped candy formed after crush
            elif match_counter == 4:
                match_counter = match_counter - 1
                self.squares[row+match_counter][col].set_striped_candy(candy.color,StripedCandy.DIR[1])
            # Match 5; chocolate formed after crush
            else:
                match_counter = match_counter - 1
                self.squares[row+match_counter][col].set_chocolate()

            return True

    # Fill empty spaces with upper candy
    # Refill top rows with new candy
    # Start from bottom-right and go left (i.e. opposite)
    def move_and_refill(self):
        for row in range(self.rows-1,-1,-1):
            for col in range(self.cols-1,-1,-1):
                if self.squares[row][col].candy == None:
                    for new_row in range(row-1,-1,-1):
                        if self.squares[new_row][col].candy != None:
                            self.squares[row][col].candy = self.squares[new_row][col].candy
                            self.squares[new_row][col].candy = None
                            break
                    # If we found no upper candy, create a new random one
                    if self.squares[row][col].candy == None:
                        self.squares[row][col].set_candy()

    def print_info(self):
        self.time_elapsed = time.time()-self.start_time
        #print("Time Elapsed: "+str(self.time_elapsed))
        #print("Total Moves: "+str(self.move_counter))
        #print("Total Score: "+str(self.score))
        if hasattr(self, 'active_jelly'):
            if self.active_jelly > 0:
                print("Jelly Remaining: "+str(self.active_jelly))

    def print_board(self):
        for row in range(len(self.squares)):
            for col in range(len(self.squares[row])):
                print(self.squares[row][col].print_square().rjust(3), end=" ")
            print()

    def hash_key(self):
        key = ''
        for row in range(len(self.squares)):
            for col in range(len(self.squares[row])):
                key = key + self.squares[row][col].print_square()
        return key

    def state_compare_diff(self, agameboard):
        diff = 0
        for row in range(len(self.squares)):
            for col in range(len(self.squares[row])):
                if self.squares[row][col].print_square() != agameboard.squares[row][col].print_square():
                    diff = diff + 1
        return diff

class Square:
    def __init__(self):
        self.jelly = False
        self.candy = Candy()    # Init with random Candy

    def copyme(self):
        copyTo = Square()
        copyTo.jelly = self.jelly
        copyTo.candy = self.candy.copyme()
        return copyTo

    def set_jelly(self):
        if self.jelly == False:
            self.jelly = True
        else:
            raise Exception("Already jellied")

    def print_square(self):
        if self.jelly == True:
            if self.candy != None:
                return self.candy.print_color()+"J"
            else:
                return "_"+"J"
        elif self.candy != None:
            return self.candy.print_color()
        else:
            return "_"

    def set_candy(self, color=None):
        if self.candy != None:
            raise Exception("Overriding candy")

        self.candy = Candy(color)

    def set_striped_candy(self, color=None, direction=None):
        if self.candy != None:
            raise Exception("Overriding candy")

        self.candy = StripedCandy(color, direction)

    def set_chocolate(self):
        if self.candy != None:
            raise Exception("Overriding candy")
        
        self.candy = Chocolate()

class Candy:
    #COLORS = ["R", "G", "B"]
    COLORS = ["R", "G", "B", "O", "Y", "P"]

    def __init__(self, color=None):
        # If no color specified, make it a random color
        if color == None:
            rand_num = random.randrange(len(Candy.COLORS))
            self.color = Candy.COLORS[rand_num]
        elif color in Candy.COLORS:
            self.color = color
        else:
            print("Not a valid color type: "+str(color))
            raise Exception("Not a valid color type: "+str(color))

    def copyme(self):
        copyTo = Candy(self.color)
        return copyTo
        
    def print_color(self):
        return self.color

class StripedCandy(Candy):
    DIR = ["v", "h"]

    def __init__(self, color=None, direction=None):
        super().__init__(color)
        # If no direction specified, make it a random direction
        if direction == None:
            rand_num = random.randrange(len(StripedCandy.DIR))
            self.direction = StripedCandy.DIR[rand_num]
        elif direction in StripedCandy.DIR:
            self.direction = direction
        else:
            print("Not a valid striped candy direction")
            raise Exception("Not a valid striped candy direction")

    def copyme(self):
        copyTo = StripedCandy(self.color,self.direction)
        return copyTo

    def print_color(self):
        if self.direction == StripedCandy.DIR[0]:
            return self.color+"V"
        else:
            return self.color+"H"

# Chocolate has its own unique "color" (really all colors)
class Chocolate:
    def __init__(self):
        self.color = "C"
        self.exploding = False  # Lets game know to crush this asap

    def copyme(self):
        copyTo = Chocolate()
        copyTo.exploding = self.exploding
        return copyTo

    def print_color(self):
        return self.color

if __name__ == "__main__":
    test = Driver()
    goals = {"score":5000,"moves":1,"jelly":10}
    test.append_game(5,5,"main")
    test.append_player("human")
    test.play_game(0,0,goals)
