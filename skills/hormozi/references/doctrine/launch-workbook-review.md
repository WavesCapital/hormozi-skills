# Read the Launch Workbook as a Plan

Use this for the Money Models Book Launch Run of Show Blackbook workbook. It is a plan for one 2025 launch. It is not the master DOCX or proof that its systems worked.

Writing rule: `HZ-SYN-004`. Keep the thought deep and the words easy.

Exact source key: `100m-money-models-book-launch-all-assets-100m-money-models-100m-money-models-boo:8928f8cce6a2`.

Find the original XLSX through the file manifest or source reader. Cite its checked path and sheet cells. The PDF splits rows across pages and clips some cells. Read the native sheet when fields must stay together. Read the original embedded images for the call flows.

## Send the Right Message to the Right Person

In `EmailSMSMailers`, columns B:H hold each message's send type, campaign, title, time, subject, channel and audience. Column A is a separate resource list and color key. Do not attach its words to the message on the same row.

The cell fill names the planned sender or task: yellow is Shopify, gray is HubSpot, peach is a timed HubSpot send, red needs number edits, and blue is Mailgun. Those colors do not prove anything was sent. Check the key in A4:A8 and the actual message cells.

Some rows conflict. G30:H31 reverse the General and VIP SMS labels and lists. D119 names affiliate drawing winners, but H119 names VIP winners. Row 118 puts ranked and drawing winners under a subject that says they made the Top 50. Do not pick a column by guess or grant a rank someone did not earn.

Use the buyer's current state. A person who bought needs the right receipt and access. They should not keep getting a pitch for the same purchase. A list name does not prove consent to email or text.

Source: `EmailSMSMailers!A1:H13,G30:H31,B118:H119`; PDF pages 40–55 show the split table.

## Keep the Price and Access Terms Intact

`Products & Offers!B17:G18` lists one physical book and 199 codes in the 200 bundle. The 15-book add-on brings it to 214 codes. The cart is $5,998 + $449.85 = $6,447.85, plus the stated shipping. Do not turn the bundle's name into a count of codes.

In `Launch Flows!C19`, the 200 buyer gets the Launch Workshop only if they were already VIP. The Implementation Workshop is a different benefit. Keep that buyer-history rule when explaining the offer. Do not give every buyer every benefit from a nearby row.

The 800 offer adds a six-payment plan: $3,000 now is the first of six, not an extra payment. The total is $18,000. A small first payment does not make the whole offer cheap or free.

Source: `Products & Offers!B17:G19` and `Launch Flows!C17:E20`; PDF pages 1–9 and 26–31. These are this workbook's terms, not current offers.

## Check the Clock, Not Just the Countdown

Use one checked event time and expiry for a new plan. This sheet mixes dates, time zones, rough stage times and fixed delays. A “live now” subject is not ready just because its row has a date.

For example, the 7:45 reminder says 60 minutes, but another sheet starts at 9. The 8:30pm cart email says three hours to midnight; it is three and a half. The Skool email at 7pm says two hours until 11:59pm; it is four hours and 59 minutes. The source does not say why these lines differ.

Keep a trigger such as “after the second speaker” tied to that event. Do not treat its rough clock time as the trigger. Check that a delayed cart message cannot go out after purchase or expiry.

Source: `EmailSMSMailers!D34:H47,D55:H56,D94:H94`. Event durations also conflict within `Events!B3:G7`. Check the named event rather than blending drafts.

## Make Help Easy to Reach

The three images on `Sales Flow` show call routing, failed-transfer fallbacks, holding, callbacks and a short rating after the call. Use the arrows as well as the labels. The public menu has four choices, but all four unknown-caller paths lead to queue 4. Four choices do not prove four separate teams.

Keep a fallback when the first person cannot answer. Offer a callback only if the system can keep the promised place. The drawing gives no maximum wait value. Its $500k cutoff, vendor and queue numbers belong to this launch; they are not rules for every business.

Source: `Sales Flow`, original `xl/media/image1.png` through `image3.png`; PDF pages 14–19 split these images.

## A Plan Is Not Proof

“Done” on `Launch Flows` is a sheet label, not proof that a checkout or delivery works. The asset tracker has placeholder links. `Links  URLs` has blank destination columns even where a description has a real link. A join-link click is not proof someone watched.

Use those rows to ask what must work. Check the actual path before promising it does. Do not open a checkout or change a campaign just to read this source. For the broader launch method, return to [the launch guide](launch-review.md).
