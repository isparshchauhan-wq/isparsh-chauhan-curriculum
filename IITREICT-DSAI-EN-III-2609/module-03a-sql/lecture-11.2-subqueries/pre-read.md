## <span style="color:#2F7DDE">Subqueries</span>

### <span style="color:#2F7DDE">Mental Map</span>

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 45, 'rankSpacing': 55, 'padding': 20}}}%%
flowchart TB
  CUR["<b>Current Session</b><br/>Subqueries"]
  Q["<b>The Big Question</b><br/><i>What smaller question would help you answer a bigger one?</i>"]
  CV["<b>Course use case</b><br/>Find products that cost more than the average price across 20 products."]
  RL["<b>Real-world example</b><br/>Compare what regulars spent at a breakfast stall."]

  CUR ==> Q
  Q ==>|&nbsp;Used in the course&nbsp;| CV
  Q ==>|&nbsp;Seen in real life&nbsp;| RL

  classDef currSes fill:#ffe0b2,stroke:#ef6c00,color:#4e342e,stroke-width:3px
  classDef ask fill:#e3f2fd,stroke:#1565c0,color:#0d47a1,stroke-width:3px
  classDef val fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20

  class CUR currSes
  class Q ask
  class CV,RL val

  linkStyle default stroke-width:3px
```

---

### <span style="color:#2F7DDE">What You'll Learn</span>

Have you ever wondered how a breakfast stall owner spots who spent more than the group average?

By the end of this session, you will be able to:

- <span style="color:#D9660B">**Use**</span> today's average both to pick names and to show the average beside each bill.
- <span style="color:#D9660B">**Determine**</span> which of the three regulars spent above today's average.
- <span style="color:#D9660B">**Compare**</span> one average shared by all three regulars with a last bill that depends on whose name you're reading.
- <span style="color:#D9660B">**Write**</span> a smaller question that finds today's average for the three regulars so a larger question can use it.

> <span style="color:#2F7DDE">**Topics you will meet:**</span> Subqueries, Nested Queries.
>
> Join the session to learn each of these in detail.

---

### <span style="color:#2F7DDE">Why You Are Learning This Topic</span>

You stop at the same stall for breakfast before class. Today you add a cup of tea to your order. The owner writes down each regular's total after they pay. She wants to see whose bill was above the average for those regulars today. She also wonders who spent more than on their own last visit.

A <span style="color:#D9660B">**subquery**</span> means a question inside a larger request for data, where the larger request uses its answer.

In this course, you'll use smaller questions like these to decide what belongs in a report.

> <span style="color:#2F7DDE">**Think about it:**</span> What number would the owner need before deciding whether your bill was above today's average?

---

### <span style="color:#2F7DDE">The Breakfast Stall Puzzle</span>

Each row gives one regular's bill from their last visit and their bill from today, in rupees.

| Regular | Last visit (₹) | Today (₹) |
|:-------:|:--------------:|:---------:|
| Asha | 80 | 90 |
| Isha | 150 | 130 |
| Dev | 140 | 170 |

<span style="color:#D9660B">**What you want to happen:**</span>

- Keep only the names with bills above today's average.
- Show today's average beside each regular's bill in a full list.
- Match each regular's bill today to their own last bill.

> <span style="color:#D9660B">**Wonder about this:**</span>
>
> - Should a bill equal to the average make the first list?
> - Whose last bill would you look up when you reach Dev's row?

---

### <span style="color:#2F7DDE">Think It Through</span>

There is no wrong first try. Keep your guesses for the session.

**1. What is the average bill for the three regulars today?**

Hint: Add today's three bills and share the total equally.

**2. Which names would you keep if the owner wants bills above that average?**

Hint: Check each amount in the Today column against your first answer.

**3. Would Asha make the list if each regular had to spend more than on their last visit?**

Hint: Look at the two bills in Asha's row.

---

### <span style="color:#2F7DDE">One Question to Carry Into the Session</span>

> <span style="color:#2F7DDE">**How can one request ask for a number and use it to decide which names to show?**</span>
>
> What changes if the number you need depends on whose row you're reading?
