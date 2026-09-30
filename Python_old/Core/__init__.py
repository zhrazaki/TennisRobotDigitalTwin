"""
Purpose:     Marks 'Core' as an importable package. Core contains the
             single-source-of-truth court configuration and coordinate
             system used by every later phase (surface, lines, net,
             fence, lighting, etc). Nothing in Core should import
             from Court/, Environment/, or Tools/.
Dependencies: None
Inputs:      None
Outputs:     None
"""
