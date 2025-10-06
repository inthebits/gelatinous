"""
Custom EvTable subclass with proper Unicode box-drawing character support.

This module provides a BoxTable class that extends EvTable to properly render
tables using Unicode box-drawing characters including proper T-junctions and
crosses at intersections.
"""

from evennia.utils.evtable import EvTable
from evennia.utils.ansi import ANSIString


class BoxTable(EvTable):
    """
    Custom EvTable that uses Unicode box-drawing characters.
    
    This subclass overrides EvTable's border rendering to properly use
    box-drawing characters including:
    - Corners: ┌ ┐ └ ┘
    - Lines: ─ │
    - T-junctions: ┬ ┴ ├ ┤
    - Cross: ┼
    
    Usage:
        from world.utils.boxtable import BoxTable
        
        table = BoxTable("Header1", "Header2", "Header3")
        table.add_row("data1", "data2", "data3")
        print(table)
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize BoxTable with Unicode box-drawing characters.
        
        Args:
            *args: Column headers
            **kwargs: Same as EvTable, but border characters are preset
        """
        # Set default box-drawing characters
        kwargs.setdefault('border', 'cells')
        kwargs.setdefault('border_left_char', '│')
        kwargs.setdefault('border_right_char', '│')
        kwargs.setdefault('border_top_char', '─')
        kwargs.setdefault('border_bottom_char', '─')
        kwargs.setdefault('corner_top_left_char', '┌')
        kwargs.setdefault('corner_top_right_char', '┐')
        kwargs.setdefault('corner_bottom_left_char', '└')
        kwargs.setdefault('corner_bottom_right_char', '┘')
        kwargs.setdefault('header_line_char', '─')
        
        # Initialize parent
        super().__init__(*args, **kwargs)
    
    def _generate_lines(self):
        """
        Override line generation to fix T-junctions and crosses.
        
        This method post-processes the table output to replace incorrect
        corner characters at T-junctions with proper box-drawing characters.
        """
        # Get original lines from parent
        lines = list(super()._generate_lines())
        
        if not lines or len(lines) < 3:
            return lines
        
        # Process each line to fix intersections
        fixed_lines = []
        for i, line in enumerate(lines):
            line_str = str(line)
            
            # Fix T-junctions and crosses
            if i == 0:
                # Top line: replace + with ┬ for column junctions
                line_str = self._fix_top_line(line_str)
            elif i == len(lines) - 1:
                # Bottom line: replace + with ┴ for column junctions
                line_str = self._fix_bottom_line(line_str)
            else:
                # Middle lines: fix left/right edges and crosses
                line_str = self._fix_middle_line(line_str)
            
            fixed_lines.append(ANSIString(line_str))
        
        return fixed_lines
    
    def _fix_top_line(self, line):
        """
        Fix top line T-junctions.
        
        Replaces + characters (except corners) with ┬ for downward T-junctions.
        """
        if not line:
            return line
        
        # Convert to list for easy manipulation
        chars = list(line)
        
        # Find all + characters and replace with ┬ (except first and last)
        for i in range(1, len(chars) - 1):
            if chars[i] == '+':
                chars[i] = '┬'
        
        return ''.join(chars)
    
    def _fix_bottom_line(self, line):
        """
        Fix bottom line T-junctions.
        
        Replaces + characters (except corners) with ┴ for upward T-junctions.
        """
        if not line:
            return line
        
        # Convert to list for easy manipulation
        chars = list(line)
        
        # Find all + characters and replace with ┴ (except first and last)
        for i in range(1, len(chars) - 1):
            if chars[i] == '+':
                chars[i] = '┴'
        
        return ''.join(chars)
    
    def _fix_middle_line(self, line):
        """
        Fix middle line intersections.
        
        Replaces:
        - + at start of line with ├
        - + at end of line with ┤
        - + in middle with ┼
        """
        if not line:
            return line
        
        # Convert to list for easy manipulation
        chars = list(line)
        
        # Fix left edge T-junction
        if len(chars) > 0 and chars[0] == '+':
            chars[0] = '├'
        
        # Fix right edge T-junction
        if len(chars) > 1 and chars[-1] == '+':
            chars[-1] = '┤'
        
        # Fix internal crosses
        for i in range(1, len(chars) - 1):
            if chars[i] == '+':
                chars[i] = '┼'
        
        return ''.join(chars)


class SimpleBoxTable(EvTable):
    """
    Simplified BoxTable without internal column/row borders.
    
    This creates a clean table with just an outer box and header separator.
    Useful for cleaner displays without grid lines.
    
    Usage:
        from world.utils.boxtable import SimpleBoxTable
        
        table = SimpleBoxTable("Header1", "Header2")
        table.add_row("data1", "data2")
        print(table)
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize SimpleBoxTable with outer box and header line only.
        
        Args:
            *args: Column headers
            **kwargs: Same as EvTable
        """
        # Set default box-drawing characters for simple box
        kwargs.setdefault('border', 'table')  # Only outer border
        kwargs.setdefault('border_left_char', '│')
        kwargs.setdefault('border_right_char', '│')
        kwargs.setdefault('border_top_char', '─')
        kwargs.setdefault('border_bottom_char', '─')
        kwargs.setdefault('corner_top_left_char', '┌')
        kwargs.setdefault('corner_top_right_char', '┐')
        kwargs.setdefault('corner_bottom_left_char', '└')
        kwargs.setdefault('corner_bottom_right_char', '┘')
        kwargs.setdefault('header_line_char', '─')
        
        # Initialize parent
        super().__init__(*args, **kwargs)
    
    def _generate_lines(self):
        """
        Override to add header line to 'table' border style.
        
        The 'table' border style doesn't include a header line by default,
        so we add it manually.
        """
        lines = list(super()._generate_lines())
        
        if not lines or len(lines) < 3 or not self.header:
            return lines
        
        # Insert header line after the first data row (after header row)
        # Find the width of the table
        if lines:
            table_width = len(str(lines[0]))
            header_line = '├' + '─' * (table_width - 2) + '┤'
            
            # Insert after second line (header row)
            if len(lines) > 2:
                lines.insert(2, ANSIString(header_line))
        
        return lines
