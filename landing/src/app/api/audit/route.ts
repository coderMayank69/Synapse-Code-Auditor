import Groq from "groq-sdk";
import { NextRequest, NextResponse } from "next/server";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const SYSTEM_PROMPT = `You are Synapse Code Auditor — an expert AI code reviewer specializing in security vulnerabilities, performance issues, concurrency bugs, and architectural problems.

When reviewing code, provide:
1. 🔴 Critical Issues (security, crashes, data loss)
2. 🟡 Warnings (performance, reliability, best practices)
3. 🟢 Suggestions (refactoring, readability, maintainability)
4. ✅ A short corrected version of the code (if applicable)
5. 📊 An overall quality score from 0–100

Format your response in clear Markdown with emoji indicators. Be concise, actionable, and developer-friendly.`;

export async function POST(req: NextRequest) {
  try {
    const { code, language = "python" } = await req.json();

    if (!code || code.trim().length === 0) {
      return NextResponse.json({ error: "No code provided" }, { status: 400 });
    }

    if (code.length > 8000) {
      return NextResponse.json(
        { error: "Code too long (max 8000 characters)" },
        { status: 400 }
      );
    }

    const completion = await groq.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      temperature: 0.2,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        {
          role: "user",
          content: `Please audit the following ${language} code:\n\n\`\`\`${language}\n${code}\n\`\`\``,
        },
      ],
    });

    const content = completion.choices[0]?.message?.content ?? "No review generated.";

    return NextResponse.json({
      review: content,
      model: completion.model,
      usage: completion.usage,
    });
  } catch (err: unknown) {
    console.error("[audit] Error:", err);
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
