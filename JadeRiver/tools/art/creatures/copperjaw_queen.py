"""Copperjaw Queen - the Copperjaw swarm once a Queen has risen in the box (Metal).

The same cloud as ``copperjaw_swarm`` with a large gold-cased Queen wearing a pale-gold
crown at its heart; she leads the lance and falls with the rest.
"""
import copperjaw_swarm as base

SPEC = dict(base.SPEC, id="copperjaw_queen")


def draw(cv, action, frame):
    base.draw(cv, action, frame, queen=True)
