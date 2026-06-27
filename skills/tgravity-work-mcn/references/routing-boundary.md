# MCN Routing Boundary

Use this file only when the router must resolve an ambiguous MCN asset request.

## Ambiguous Examples

`今天这个达人接了某品牌一个小红书合作，结果一般。`

Route to `tgravity-work-mcn-collaboration`, because it contains an execution fact.

`今天这个达人感觉适合某品牌。`

Route to `tgravity-work-mcn-creator-profile` if the user is describing the creator; route to `tgravity-work-mcn-brief-builder` if the user is matching against a known brand need.

`这个品牌想找几个 AI 垂类达人。`

Route to `tgravity-work-mcn-brief-builder`, because it is a demand/brief.

`这个品牌是朋友介绍的，预算可能还行。`

Route to `tgravity-work-mcn-brand-profile`.
