import math
from src.cc_simulator import Driver

class AITester:
    def __init__(self, num_runs, goals, width, height, depth_limit, beam_width):
        self.num_runs = num_runs
        self.depth_limit = depth_limit
        self.beam_width = beam_width
        self.goals = goals
        self.width = width
        self.height = height
        self.final_boards = []
        self.issmart = True
    
    def start(self):
        score = 0
        moves = 0
        time_elapsed = 0
        seed = 0
        num_children = 0
        if self.issmart == True:
            stored_states = None
            for i in range(self.num_runs):
                print("Starting Run #"+str(i+1))
                seed = seed + 1
                test = Driver(seed)
                test.append_game(self.height,self.width,"main")
                test.append_player("ai",self.depth_limit,self.beam_width)
                if stored_states != None:
                    test.players[0].stored_states = stored_states
                test.play_game(0,0,self.goals)
                num_children = num_children + test.players[0].num_children
                if stored_states == None:
                    stored_states = test.players[0].stored_states
                score = score + test.gameBoards[0].score
                moves = moves + test.gameBoards[0].move_counter
                time_elapsed = time_elapsed + test.gameBoards[0].time_elapsed
                self.final_boards.append(test.gameBoards[0])
                avg_score = score/len(self.final_boards)
                print("Average Score: "+str(avg_score))
                #print("Average Time: "+str(time_elapsed/len(self.final_boards)))
                #print("Length of stored states: "+str(len(stored_states)))
                #print("Hash hits: "+str(test.players[0].hash_hits))
        else:
             for i in range(self.num_runs):
                print("Starting Run #"+str(i+1))
                seed = seed + 1
                test = Driver(seed)
                test.append_game(self.height,self.width,"main")
                test.append_player("random")
                test.play_game(0,0,self.goals)
                score = score + test.gameBoards[0].score
                moves = moves + test.gameBoards[0].move_counter
                time_elapsed = time_elapsed + test.gameBoards[0].time_elapsed
                self.final_boards.append(test.gameBoards[0])
                avg_score = score/len(self.final_boards)

        # Average stats
        std_dev = 0
        children = 0
        for i in self.final_boards:
            std_dev = std_dev + math.pow(i.score-avg_score,2)
        std_dev = std_dev / len(self.final_boards)
        std_dev = math.sqrt(std_dev)

        #conf_low = math.sqrt( ((self.num_runs-1)*math.pow(std_dev,2))/(math.pow(avg_score,2)*((1-0.95)/2)) )
        #conf_high = math.sqrt( ((self.num_runs-1)*math.pow(std_dev,2))/(math.pow(avg_score,2)*((1+0.95)/2)) )

        print("Board Size: "+str(self.width)+","+str(self.height))
        print("Depth Limit: "+str(self.depth_limit))
        print("Beam Width: "+str(self.beam_width))
        print("Average # Children: "+str(num_children/(self.goals["moves"]*self.num_runs)))
        print("Average Score: "+str(avg_score))
        print("Std Dev. Score: "+str(std_dev))
        #print("95% Confidence: ("+str(conf_high)+","+str(conf_low)+")")
        print("Average Moves: "+str(moves/len(self.final_boards)))
        print("Average Time: "+str(time_elapsed/len(self.final_boards)))
        self.final_boards.sort(key=lambda final_board: final_board.score)
        print("Median Score: "+str(self.final_boards[int(len(self.final_boards)/2)].score))

if __name__ == "__main__":
    test = AITester(10,{"score":5000000,"moves":5},10,10,3,9)
    test.issmart = False
    test.start()
