# Work in progress - Sudoku puzzle generator
""" To Do;
- Rework code into a custom library with classes and methods
- look at making sure there is a single solution
- Tidy up the formats of the outputs
"""

# Import necessary libraries
import random
import copy

# Global variables
N = 9  # Size of the Sudoku grid
NUMBERS = list(range(1, N + 1)) # Numbers 1-9

def print_board(board, title="Sudoku Board"):
    """Prints the Sudoku board in a clean, grid format."""
    print(f"\n--- {title} ---")
    for i in range(N):
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - - - ")

        for j in range(N):
            if j % 3 == 0 and j != 0:
                print(" | ", end="")

            # Use '.' for empty cells (0)
            print(f" {board[i][j] if board[i][j] != 0 else '.'}", end="")
        print()
    print("-------------------\n")

def is_safe(board, row, col, num):
    """
    Checks if it's safe to place 'num' at board[row][col] by ensuring 
    it doesn't violate row, column, or 3x3 box rules.
    """
    # Check row
    if num in board[row]:
        return False

    # Check column
    for i in range(N):
        if board[i][col] == num:
            return False

    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False

    return True

def find_empty_cell(board):
    """Finds the next empty cell (represented by 0) in the board."""
    for i in range(N):
        for j in range(N):
            if board[i][j] == 0:
                return i, j
    return None, None

def fill_grid(board):
    """
    Recursive backtracking function to fill the entire 9x9 grid randomly
    to create a solved Sudoku puzzle.
    """
    row, col = find_empty_cell(board)

    # Base case: If no empty cells are found, the grid is solved.
    if row is None:
        return True

    # Try numbers 1-9 in a random order
    numbers_to_try = list(NUMBERS)
    random.shuffle(numbers_to_try)

    for num in numbers_to_try:
        if is_safe(board, row, col, num):
            board[row][col] = num  # Place the number

            if fill_grid(board):
                return True # Puzzle successfully filled

            # If the current placement leads to a failure, backtrack
            board[row][col] = 0

    # Trigger backtracking
    return False

def create_puzzle(solved_board, cells_to_remove):
    """
    Removes numbers from the solved board to create the puzzle.
    
    NOTE: A simple generator like this doesn't guarantee unique solvability,
    which is a complex problem. It just ensures a certain number of cells are empty.
    """
    # Create a copy so we don't modify the solved board
    puzzle_board = copy.deepcopy(solved_board)
    
    # Store the coordinates of all cells
    all_coords = [(r, c) for r in range(N) for c in range(N)]
    random.shuffle(all_coords)

    # Remove the specified number of cells
    for i in range(cells_to_remove):
        if not all_coords:
            break  # Stop if all cells are removed
        
        row, col = all_coords.pop()
        puzzle_board[row][col] = 0
        
    return puzzle_board

def generate_sudoku(cells_to_remove=40):

    """Generates a Sudoku puzzle with a specified number of cells removed."""
    # Step 1: Create an empty board
    board = [[0 for _ in range(N)] for _ in range(N)]

    # Step 2: Fill the board to create a solved Sudoku puzzle
    fill_grid(board)

    # Step 3: Create the puzzle by removing cells
    puzzle = create_puzzle(board, cells_to_remove)

    return puzzle, board  # Return both the puzzle and the solved board

if __name__ == "__main__":
    # Generate a Sudoku puzzle
    puzzle, solution = generate_sudoku(cells_to_remove=40)

    # Print the generated puzzle and its solution
    print_board(puzzle, title="---- Puzzle ----")
    print_board(solution, title="--- Solution ---")