# Low-clutter Orca operations

## Contents

- [Meaning before labels](#meaning-before-labels)
- [Inventory and identity](#inventory-and-identity)
- [Supported mutation and visible proof](#supported-mutation-and-visible-proof)
- [Old-branch cleanup](#old-branch-cleanup)
- [Completion evidence](#completion-evidence)

## Meaning before labels

Use actual `Projects`, `Areas`, `Resources`, and `Archives` groups when the operator requests PARA.
Treat these as operating semantics, not a mandate to mirror numbered vault folders or impose PARA on another operator.
A finite outcome belongs in Projects; an ongoing responsibility belongs in Areas; reusable material belongs in Resources; explicitly finished or inactive work belongs in Archives.
Separate a logical work target from its Git repositories: one target can contain an intentional multi-repository cluster.
Keep each repository's verified Git identity distinct even when the interface groups them under that target.
An Orca project is not necessarily a finite PARA project: an Area can contain short-lived task workspaces.
Preserve an explicitly completed status and Archives membership unless the operator changes that decision.

| Surface | Owns | Naming rule |
|---|---|---|
| Top-level group | One PARA classification | Use the full group name once |
| Project | Verified repository or intentional cluster | Use the operator's recognizable target name |
| Workspace | Concrete task or execution context | Preserve meaningful task names and parent-child relationships |
| Host | Execution location | Use host metadata rather than repeating it in every label |
| Agent role | Responsibility or persona | Keep roles distinct even when they share a repository |

For a source repository and a separate backup repository serving one knowledge system, prefer one recognizable visual cluster with purpose labels such as source and backup.
Use host metadata for remote execution location rather than creating a second conceptual project called Remote.
Discover whether the installed version supports the needed multi-repository grouping or nesting; if it does not, report that boundary instead of falsifying origins or upstream fields to force a shared canonical ID.

Prefer reversible grouping, nesting, and view changes over removal when the goal is visual clarity.
Treat sleep, archive, and delete as distinct effects: discover their current semantics before using them.
In particular, sleep can close panels and workspace deletion can remove files; neither is merely hiding a row.

## Inventory and identity

1. Discover the installed Orca CLI and the Orca application's bundled command guide before relying on remembered flags or API payloads.
2. Inventory the authorized connected hosts, repositories, groups, workspace IDs and paths, statuses, and terminal IDs; record disconnected hosts as unverified.
3. Inspect the actual Git root and origin on each host, with only narrow metadata reads.
4. Match the provider, owner, and repository identity, then compare Orca's canonical project and source setup IDs.
5. Verify fork and upstream relationships with actual Git/provider evidence before correcting stale metadata or combining cards.
6. Reuse a matching local checkout; create a tracked-source clone only within the approved setup scope.
7. Assign the shared identity to its local group and verify the remote setup remains attached to that identity.

A parent-folder registration can contain multiple Git repositories.
Register and connect those real roots individually; keep an active umbrella-folder workspace intact rather than pretending it is one repository.
Different origins are not duplicates merely because a stale upstream field gives them the same canonical ID.
Multiple live setups for one identity can also be intentional; preserving them is preferable to a destructive deduplication.
Do not print embedded credentials from remote URLs or copy home directories, authentication files, untracked agent state, or private runtime configuration into a counterpart checkout.
Reuse approved configured authentication in bounded, non-interactive mode; if it is unavailable, leave the clone pending and report the operator authentication step instead of waiting on a credential prompt.
Do not embed a token in a remote URL or provision new credentials as part of grouping.

## Supported mutation and visible proof

Use the discovered native CLI, supported runtime API, or native UI.
An advertised schema field can still be filtered or ignored; require read-back of every intended effect.
Do not edit internal state files, hardcode bundle internals, or turn a failed private API experiment into a reusable command.
If the installed version has no supported operation, retain the current state and name the missing capability.

Group placement can depend on which host setup represents a shared project and on native ordering.
Verify that behavior on the installed version rather than assuming every host registration needs its own PARA group.
Remove an obsolete group only after repositories, folder workspaces, and child-group references are all absent; disable any cascading removal option.
Do not remove a setup used by a terminal to simplify representative selection.
A rename or grouping request does not authorize setup removal.
Even an explicit request to delete a duplicate-looking setup leaves live or unverified-identity setups protected in this workflow; a separate removal decision needs verified identity, concrete effects, and an approved session-preservation or termination plan.

Inspect actual group expansion, project placement, host workspaces, and visible tab labels after read-back.
A process/OSC title is not necessarily the custom title rendered on a tab.
Use fresh UI element identities; do not replay stale coordinates.
If a supported refresh is necessary, preserve terminal IDs before and after; a full restart is not a substitute.
An inaccessible UI leaves visible placement unverified even if metadata is correct.

## Old-branch cleanup

Treat a cleanup request as permission for the scoped safe candidates, not blanket permission to erase old context.
Default to local branch refs only; remote-host local branches, remote-tracking pruning, and server-side remote branches are separate scopes.
Use 30 days as a conservative inactivity default and state it; use a different threshold only when the operator specifies it.
Age is eligibility evidence, not proof of abandonment.

Audit first and record candidate names, tip OIDs, default refs, age evidence, and retention reasons before mutation.
Apply all of these gates:

| Gate | Keep the branch when |
|---|---|
| Ownership | It is a default, release, deployment, or intentionally shared branch |
| Activity | Its tip commit or latest branch reflog update is newer than the cutoff |
| Evidence | The branch reflog, actual default, ancestry, or host scope is unknown |
| Worktrees | Any registered Git worktree checks it out, including one outside Orca |
| Reachability | Its tip is not an ancestor of both the verified local default and its remote-tracking default |
| Concurrency | The audited tip, relevant defaults, worktree usage, or session associations change |

Use read-only Git probes such as `git worktree list --porcelain`, `git for-each-ref`, `git reflog show`, and `git merge-base --is-ancestor` through the Git workflow.
A commit timestamp is not a branch-creation timestamp; an old commit with a newly created branch stays.
Remote-tracking state is cached evidence, not proof of current server state; preserve candidates when a current default or reset is in doubt.
Coordinate concurrent writers and revalidate immediately before each deletion; if stable evidence cannot be established, keep the branch.

Use only non-forced `git branch -d` on the revalidated named candidates.
Its upstream/HEAD merge check does not replace the stricter two-default ancestry gate above.
If Git refuses, record the reason and keep the branch; do not escalate to `-D`, raw ref deletion, or a force-delete API.
Do not remove a worktree to make its branch eligible, and do not stash, reset, or discard dirty or untracked files.
Deleting refs is not permission to delete workspace directories, terminate sessions, or mark unfinished tasks completed.

## Completion evidence

Verify deleted refs are absent; compare retained refs and HEAD OIDs, Git worktree registrations, Orca setup IDs and paths, statuses, and terminal IDs against the inventory.
Report concurrent changes rather than overwriting them to make a comparison pass.
Separate runtime verification, visible UI verification, Git preservation, and unreachable-host coverage.
Return concise actual results and retained-item reasons; zero safe deletions is a valid successful audit.
