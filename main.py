"""
    Filename: main.py
    Author: Gregory McAdams
    E-mail: gmcadams1@comcast.net
"""
import sys
from src.runner import AITester

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: <# games> <# moves per game> <# rows> <# cols>")
        sys.exit()
    
    player_type = input("Is player smart?(y or n)")
    if player_type == 'y':
        depth = int(input("Enter max tree depth:"))
        beam_width = int(input("Enter beam width:"))
        test = AITester(int(sys.argv[1]),
                {"score":5000000,"moves":int(sys.argv[2])},
                int(sys.argv[3]),int(sys.argv[4]),depth,beam_width)
        test.issmart = True
    else:
        test = AITester(int(sys.argv[1]),
                {"score":5000000,"moves":int(sys.argv[2])},
                int(sys.argv[3]),int(sys.argv[4]),-1,-1)
        test.issmart = False
    test.start()