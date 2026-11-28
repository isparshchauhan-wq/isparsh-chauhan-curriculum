## <span style="color:#2F7DDE">Common Table Expressions (CTEs)</span>

### <span style="color:#2F7DDE">Mental Map</span>

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 45, 'rankSpacing': 55, 'padding': 20}}}%%
flowchart TB
  CUR["<b>Current Session</b><br/>Common Table Expressions (CTEs)"]
  Q["<b>The Big Question</b><br/><i>How can named steps make a long question easier to follow?</i>"]
  CV["<b>Course use case</b><br/>Find total sales for each of 3 stores before comparing them."]
  RL["<b>Real-world example</b><br/>Use a library return log to plan a shelf check."]

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

Have you ever wondered how a library decides which shelf needs attention first?

By the end of this session, you will be able to:

- <span style="color:#D9660B">**Use**</span> named steps to make a long question about returned books easier to read.
- <span style="color:#D9660B">**Write**</span> a named step in place of a question hidden inside another question.
- <span style="color:#D9660B">**Design**</span> a chain of named steps to group and compare the returned books.
- <span style="color:#D9660B">**Build**</span> a step-by-step way to find which shelf needs a check first.

> <span style="color:#2F7DDE">**Topics you will meet:**</span> Common Table Expressions, WITH Clause.
>
> Join the session to learn each of these in detail.

---

### <span style="color:#2F7DDE">Why You Are Learning This Topic</span>

You help at a library where books come back throughout the day. The return log lists each book and its shelf. You want to count the books waiting for each shelf. Then you want to find which shelf has the largest pile. A long question can hide these smaller steps inside one another.

A <span style="color:#D9660B">**common table expression**</span> means a named temporary result used within one question to the data.

In this course, you can use named results to make your work with data easier to follow.

> <span style="color:#2F7DDE">**Think about it:**</span> How might names help someone else follow your steps?

---

### <span style="color:#2F7DDE">Library Return Puzzle</span>

The log shows four books waiting to go back on shelves.

| Book | Shelf |
|:----:|:-----:|
| Moon Garden | Nature |
| River Birds | Nature |
| Star Voyage | Space |
| Ocean Atlas | Nature |

<span style="color:#D9660B">**What you want to happen:**</span>

- Gather the books by shelf.
- Count the books for each shelf.
- Find the shelf with the largest pile.

> <span style="color:#D9660B">**Wonder about this:**</span>
>
> - What name could you give the shelf counts?
> - How could one named step pass its result to the next?

---

### <span style="color:#2F7DDE">Think It Through</span>

There is no wrong first try. Keep your guesses for the session.

**1. Which books would you put in the same group?**
Hint: Look at the shelf names.

**2. What would you count before choosing a shelf to check?**
Hint: Think about each pile of books.

**3. How could you arrange your steps so a friend can follow them?**
Hint: Give each step a short name.

---

### <span style="color:#2F7DDE">One Question to Carry Into the Session</span>

> <span style="color:#2F7DDE">**How can named steps help you answer a question about the library log?**</span>
>
> What could change if one step used the result of another?
