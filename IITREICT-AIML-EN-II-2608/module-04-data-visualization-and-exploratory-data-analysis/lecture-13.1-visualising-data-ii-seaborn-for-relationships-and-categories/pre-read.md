## <span style="color:#2F7DDE">Visualising Data II: Seaborn for Relationships and Categories</span>

### <span style="color:#2F7DDE">Mental Map</span>

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 45, 'rankSpacing': 55, 'padding': 20}}}%%
flowchart TB
  CUR["<b>Current Session</b><br/>Visualising Data II: Seaborn for Relationships and Categories"]
  Q["<b>The Big Question</b><br/><i>How can the same table answer different questions?</i>"]
  CV["<b>Course use case</b><br/>Compare size and sale price for 100 homes before trying to predict prices."]
  RL["<b>Real-world example</b><br/>Use a bike repair log to plan the next repair day."]

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

Have you ever wondered why one bike repair takes longer than another?

By the end of this session, you will be able to:

- <span style="color:#D9660B">**Use**</span> a chart tool to show how repair times vary with bike age and repair type.
- <span style="color:#D9660B">**Demonstrate**</span>, with one dot per bike, how age, repair time and parts cost relate in pairs.
- <span style="color:#D9660B">**Compare**</span> wheel and brake jobs using bars for job counts and bars for average repair times.
- <span style="color:#D9660B">**Justify**</span> your choice of chart for a question about the next repair day.

> <span style="color:#2F7DDE">**Topics you will meet:**</span> Seaborn, Relationships, Categorical Plots.
>
> Join the session to learn each of these in detail.

---

### <span style="color:#2F7DDE">Why You Are Learning This Topic</span>

You help at a bike repair stand in your neighborhood. Each time a bike comes in, you write down the job. A rider asks how long a brake fix might take. Later, a friend asks which job came up most often. You have one sheet of notes for both questions.

A <span style="color:#D9660B">**chart**</span> means a picture that uses marks like dots or bars to show what's in your records.

In this course, you use charts to spot patterns before making a guess from your data.

> <span style="color:#2F7DDE">**Think about it:**</span> Could the most common job take less time on average than another job?

---

### <span style="color:#2F7DDE">The Bike Repair Puzzle</span>

Here are five jobs from the stand's first morning.

| Bike | Repair type | Bike age (years) | Repair time (minutes) | Parts cost (₹) |
|:----:|:-----------:|:----------------:|:---------------------:|:--------------:|
| Mira's | Wheel | 1 | 10 | 80 |
| Kabir's | Brake | 3 | 20 | 220 |
| Tara's | Wheel | 4 | 16 | 100 |
| Nila's | Brake | 6 | 24 | 260 |
| Dev's | Wheel | 7 | 22 | 140 |

<span style="color:#D9660B">**What you want to happen:**</span>

- See whether older bikes tend to take longer to fix.
- See whether jobs that take longer also cost more in parts.
- Find out which job comes up more often and which takes more time on average.

> <span style="color:#D9660B">**Wonder about this:**</span>
>
> - To compare bike age with repair time, which two numbers would you use to place Mira's dot?
> - Which pairs of numbers could you put side by side to learn more about parts costs?

---

### <span style="color:#2F7DDE">Think It Through</span>

There is no wrong first try. Keep your guesses for the session.

**1. Does every older bike take longer to fix?**

Hint: Compare Tara's row with Kabir's.

**2. What would each bar need to show if you want to find the most common job?**

Hint: Look for the column with names that repeat.

**3. What would change in those bars if riders asked about average repair times?**

Hint: Look for the column that measures time.

---

### <span style="color:#2F7DDE">One Question to Carry Into the Session</span>

> <span style="color:#2F7DDE">**Which chart would you show the person planning the next repair day?**</span>
>
> What would you ask them before picking it?
