import sys


def golomb(height):
    """
    Generate the first n terms of the Golomb sequence given the input pyramid row number.
    """

    # Golomb Sequence for height pyramid
    n = int(height / 2 * (1 + height))

    # Create a list to store Golomb sequence values
    dp = [0] * (n + 1)

    # Base case
    dp[1] = 1

    # Generate Golomb sequence
    for i in range(2, n + 1):
        dp[i] = 1 + dp[i - dp[dp[i - 1]]]

    print(f"Golomb sequence with n = {n}: {dp[1:]}")

    return dp[1:]


def print_pyramid(lst, height):
    """
    Print a pyramid using the elements of the given list.
    """

    # Calculate the number of rows needed for the pyramid
    # height = int((len(lst) * 2) ** 0.5)

    # Initialize the index for accessing elements in the list
    index = 0

    # Iterate through each row
    for i in range(1, height + 1):
        # Print spaces to align elements properly
        print(" " * (height - i), end="")

        # Print elements for the current row
        for j in range(i):
            # Check if index is still within the list range
            if index < len(lst):
                print(lst[index], end=" ")
                index += 1
            else:
                break

        # Move to the next line after printing all elements in the current row
        print()


# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <n>")
        sys.exit(1)

    n = int(sys.argv[1])
    print_pyramid(golomb(n), n)
