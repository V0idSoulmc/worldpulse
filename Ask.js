export default async function handler(req, res) {
  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { country, question, type } = req.body;

  if (!country) {
    return res.status(400).json({ error: 'Missing country' });
  }

  const GROQ_KEY = process.env.GROQ_API_KEY;
  if (!GROQ_KEY) {
    return res.status(500).json({ error: 'Server misconfigured' });
  }

  let systemPrompt, userMessage, maxTokens;

  if (type === 'info') {
    systemPrompt = `Tu es un expert géopolitique. Réponds UNIQUEMENT en JSON valide, sans backticks ni markdown, avec ces clés exactes:
{"capital":"...","population":"...","superficie":"...","pib":"...","langue":"...","monnaie":"...","systeme":"...","stabilite":"stable|tensions|conflit|guerre","religion":"...","description":"...","actualite":"...","badges":["badge1","badge2"]}
Badges valides: Démocratie, Dictature, Monarchie, Fédération, Théocratie, OTAN, UE, BRICS, G7, G20, ONU, Stable, Tensions, Conflit, Guerre, Nucléaire, Pétrole, Économie forte, En développement, Île, Enclavé, Arctique`;
    userMessage = `Pays: ${country}`;
    maxTokens = 1000;
  } else {
    systemPrompt = `Expert géopolitique. Réponds en français, concis (3-5 phrases), factuel et actuel.`;
    userMessage = `Pays: ${country}\nQuestion: ${question}`;
    maxTokens = 600;
  }

  try {
    const groqRes = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GROQ_KEY}`,
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        max_tokens: maxTokens,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userMessage },
        ],
      }),
    });

    if (!groqRes.ok) {
      const err = await groqRes.text();
      return res.status(502).json({ error: `Groq error: ${groqRes.status}`, detail: err });
    }

    const data = await groqRes.json();
    const text = data.choices?.[0]?.message?.content || '';
    return res.status(200).json({ text });
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
