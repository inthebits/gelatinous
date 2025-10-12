import re


NUMERIC_ORDINAL_REGEX = re.compile(r"^\s*(\d+)(st|nd|rd|th)?", re.IGNORECASE)

ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
}

TENS = {
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}

SCALES = {
    "hundred": 100,
    "thousand": 10 ** 3,
    "million": 10 ** 6,
    "billion": 10 ** 9,
    "trillion": 10 ** 12,
    "quadrillion": 10 ** 15,
    "quintillion": 10 ** 18,
    "sextillion": 10 ** 21,
    "septillion": 10 ** 24,
    "octillion": 10 ** 27,
    "nonillion": 10 ** 30,
    "decillion": 10 ** 33,
    "undecillion": 10 ** 36,
    "duodecillion": 10 ** 39,
    "tredecillion": 10 ** 42,
    "quattuordecillion": 10 ** 45,
    "quindecillion": 10 ** 48,
    "sexdecillion": 10 ** 51,
    "septendecillion": 10 ** 54,
    "octodecillion": 10 ** 57,
    "novemdecillion": 10 ** 60,
    "vigintillion": 10 ** 63,
}

ORDINAL_SUFFIXES = ["st", "nd", "rd", "th"]

LAST_ORDINALS = {
    "last": -1,
    "second-to-last": -2,
    "third-to-last": -3,
    "fourth-to-last": -4,
    "fifth-to-last": -5,
    "sixth-to-last": -6,
    "seventh-to-last": -7,
    "eighth-to-last": -8,
    "ninth-to-last": -9,
    "tenth-to-last": -10,
}


class OrdinalParser:
    numeric_ordinal_regex = NUMERIC_ORDINAL_REGEX
    ones = ONES
    tens = TENS
    scales = SCALES
    suffixes = ORDINAL_SUFFIXES
    last_ordindals = LAST_ORDINALS

    def clean_ordinal_word(self, word: str) -> str:
        """
        Remove ordinal suffixes ('st', 'nd', 'rd', 'th') from a word.

        Args:
            word (str): The word to clean.

        Returns:
            str: The word without ordinal suffix.
        """

        for suffix in self.suffixes:
            if word.endswith(suffix):
                return word[:-len(suffix)]
        return word

    def to_english_ordinal(self, num: int) -> str:
        """
        Convert a number into its full English ordinal word form;

        Supports very large numbers (up to 10**63) using included scales.
        Includes natural English phrasing with 'and' when appropriate.

        Args:
            num (int): The number to convert.

        Returns:
            str: The English ordinal word.
        """

        ones = {
            1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
            6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth",
        }

        tens = {
            10: "tenth", 11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth",
            15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth", 19: "nineteenth",
            20: "twentieth", 30: "thirtieth", 40: "fortieth", 50: "fiftieth",
            60: "sixtieth", 70: "seventieth", 80: "eightieth", 90: "ninetieth",
        }

        tens_prefix = {
            20: "twenty", 30: "thirty", 40: "forty", 50: "fifty",
            60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety"
        }

        # reverse the scales so we start from the largest scale
        sorted_scales = sorted(self.scales.items(), key=lambda x: x[1], reverse=True)

        def to_ordinal_words(number: int) -> str:
            """Recursively convert a positive integer to English ordinal words."""
            if number == 0:
                return "zeroth"
            if number < 10:
                return ones[number]
            if 10 <= number < 20:
                return tens[number]
            if number < 100:
                if number in tens:
                    return tens[number]
                base = (number // 10) * 10
                remainder = number % 10
                return f"{tens_prefix[base]}-{ones[remainder]}"

            # handle large scale names (hundred, thousand, million, ...)
            for name, value in sorted_scales:
                if number >= value:
                    quotient, remainder = divmod(number, value)
                    left = to_ordinal_words(quotient)

                    if remainder == 0:
                        # “one thousandth” / “three millionth”
                        return f"{left} {name}th"

                    # natural “and” phrasing for smaller remainders (<100)
                    connector = " and " if remainder < 100 else " "
                    right = to_ordinal_words(remainder)

                    # for “hundredth”, “thousandth” drop the “th” in prefix
                    return f"{left} {name}{connector}{right}"

            return str(number)

        # Negative ordinals use “to last”
        if num < 0:
            absolute_number = abs(num)
            if absolute_number == 1:
                return "last"
            return f"{to_ordinal_words(absolute_number)} to last"

        return to_ordinal_words(num)

    def parse_english_ordinal(self, words: list) -> tuple:
        """
        Parse a list of English words representing an ordinal into a numeric value.

        Handles units, teens, tens, scales (hundred, thousand, million, ...),
        hyphenated words, and the word 'and'.

        Args:
            words (list of str): List of words to parse.

        Returns:
            tuple:
                - int: Numeric value of the ordinal.
                - int: Number of words consumed from the list.
        """

        total = 0
        current = 0
        consumed = 0

        for word in words:
            clean_word = self.clean_ordinal_word(word.lower())

            if clean_word == "and":
                consumed += 1
                continue
            elif clean_word in self.ones:
                current += self.ones[clean_word]
            elif clean_word in self.tens:
                current += self.tens[clean_word]
            elif clean_word in self.scales:
                scale = self.scales[clean_word]
                if current == 0:
                    current = 1
                current *= scale
                if scale >= 1000:
                    total += current
                    current = 0
            elif "-" in clean_word:  # hyphenated word
                parts = clean_word.split("-")
                value, _ = self.parse_english_ordinal(parts)
                current += value
            else:
                break  # stop parsing at first unknown word

            consumed += 1

        total += current
        return total, consumed

    def parse(self, string: str) -> tuple:
        """
        Parse a string starting with an ordinal and return the numeric value
        and the remaining string.

        Supports:
            - Numeric ordinals (1st, 23rd, 100th)
            - English ordinals (first, twenty-first, one hundred and twenty-third)
            - Last ordinals (last, second-to-last, third-to-last, ...)
            - Hyphenated ordinals (twenty-first, forty-two-millionth)
            - Large numbers including trillions and beyond

        Args:
            string (str): Input string starting with an ordinal.

        Returns:
            tuple:
                - int or None: Numeric value of the ordinal, or None if not found.
                - str: Remaining string after the ordinal.
        """

        string = string.strip()

        words = re.findall(r"\w+(?:-\w+)?", string.lower())

        # last style ordinals
        if words:
            for length in range(3, 0, -1):
                key = "-".join(words[:length])
                if key in self.last_ordindals:
                    remaining_string = " ".join(words[length:]) if len(words) > length else ""
                    return self.last_ordindals[key], remaining_string

        # numeric ordinals
        match = self.numeric_ordinal_regex.match(string)

        if match:
            number = int(match.group(1))
            remaining_string = string[match.end():].lstrip()
            return number, remaining_string

        # fallback to normal english ordinals
        if words:
            number, consumed = self.parse_english_ordinal(words)
            if number != 0:
                remaining_words = words[consumed:]
                remaining_string = " ".join(remaining_words)
                return number, remaining_string

        return None, string
