import os

def update_file(path, replacements):
    with open(path, 'r') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)

# TripTimeline.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/TripTimeline.tsx', [
    ("wp.name || `Waypoint ${idx + 1}`", "wp.name || t`Waypoint ${idx + 1}`")
])

# AdvisoryBanner.tsx - missed Trans? No, the title is passed into JSX. Wait, in AdvisoryBanner:
# <span className={`text-[11px] font-extrabold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${config.badgeBg}`}>
#   {config.title}
# </span>
# So it will be evaluated correctly since we wrapped title in t``.

