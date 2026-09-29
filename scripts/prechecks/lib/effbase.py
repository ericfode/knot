"""The effective base: what a branch is compared against.

`merge-base(head, main)` is the wrong base for an increment stacked on another unmerged increment
(vm-core on vm-spec, literals on modules): it would charge the upstream's files to the branch. The
effective base is the descendant-most of the main merge-base and each declared upstream's merge-base
whose history reaches beyond main. When neither of two bases contains the other (a branch that merged
main and separately carried an upstream), the base is the tree of a trial merge of the two.

Upstream relations are declared, never inferred from topology: a branch created from X and X share
their first-parent history in both directions, so topology cannot tell them apart.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .gitx import Repo


@dataclass
class EffectiveBase:
    commit: str | None                 # main-side or descendant-most base commit
    tree: str | None = None            # tree-ish to diff from (== commit's tree unless a merged-bases tree)
    kind: str = 'main'                 # main | stacked | merged-bases | merged-bases-with-conflicts | none
    stacked_on: list = field(default_factory=list)   # [[upstream id, upstream tip, merge-base], ...]
    conflicts: list = field(default_factory=list)    # conflicted paths of a merged-bases tree
    main_base: str | None = None

    def treeish(self) -> str | None:
        return self.tree or self.commit


def compute(repo: Repo, head: str, main_ref: str | None, upstreams: list[dict]) -> EffectiveBase:
    main_tip = repo.rev_parse(main_ref) if main_ref else None
    base = repo.merge_base(head, main_tip) if main_tip else None
    result = EffectiveBase(commit=base, kind='main' if base else 'none', main_base=base)
    if not main_tip:
        return result
    for upstream in upstreams:
        tip = repo.rev_parse(upstream.get('tip') or upstream['ref'])
        if not tip:
            result.stacked_on.append([upstream['id'], None, None])
            continue
        shared = repo.merge_base(head, tip)
        # Only history that lies beyond main counts as stacking.
        if not shared or repo.is_ancestor(shared, main_tip):
            continue
        result.stacked_on.append([upstream['id'], tip, shared])
        current = result.commit
        if current is None or repo.is_ancestor(current, shared):
            result.commit, result.kind = shared, 'stacked'
            result.tree = None
        elif not repo.is_ancestor(shared, current):
            code, conflicts, _messages, merged = repo.merge_tree(current, shared)
            if merged:
                result.tree = merged
                result.kind = 'merged-bases' if code == 0 else 'merged-bases-with-conflicts'
                result.conflicts = conflicts
    return result
