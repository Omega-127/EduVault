package com.eduvault.service;

import com.eduvault.model.Note;
import com.eduvault.repository.LocalJsonDatabase;
import com.fasterxml.jackson.databind.ObjectMapper;
import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.DocumentSplitter;
import dev.langchain4j.data.document.Metadata;
import dev.langchain4j.data.document.splitter.DocumentSplitters;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.embedding.onnx.allminilml6v2.AllMiniLmL6V2EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingMatch;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.inmemory.InMemoryEmbeddingStore;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.io.File;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class RAGService {

    private static final Logger logger = LoggerFactory.getLogger(RAGService.class);

    private final ObjectMapper mapper = new ObjectMapper();

    private static final Set<String> STOP_WORDS = Set.of(
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
            "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
            "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
            "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
            "have", "haven't", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
            "i", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most",
            "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
            "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "should", "shouldn't",
            "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
            "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
            "wasn't", "we", "were", "weren't", "what", "when", "where", "which", "while", "who", "whom", "why",
            "with", "won't", "would", "wouldn't", "you", "your", "yours", "yourself", "yourselves", "explain",
            "describe", "give", "tell", "detail", "write"
    );

    @Value("${app.storage.local-dir}")
    private String storageDir;

    private EmbeddingModel embeddingModel;
    private EmbeddingStore<TextSegment> embeddingStore;

    @Autowired
    private GeminiService geminiService;

    @Autowired
    private LocalJsonDatabase database;

    @Value("${app.rag.onnx.enabled:false}")
    private boolean onnxEnabled;

    @PostConstruct
    public void init() {
        this.embeddingStore = new InMemoryEmbeddingStore<>();
        loadStore();

        if (!onnxEnabled) {
            logger.info("ONNX EmbeddingModel disabled by config to prevent heap exhaustion (using direct context-grounded LLM retrieval)");
            this.embeddingModel = null;
            return;
        }

        Thread initThread = new Thread(() -> {
            try {
                Thread.sleep(8000);
                logger.info("Initializing RAGService with local ONNX embeddings in background...");
                this.embeddingModel = new AllMiniLmL6V2EmbeddingModel();
                logger.info("RAGService ONNX embeddings initialized successfully");
            } catch (Throwable e) {
                logger.warn("ONNX EmbeddingModel disabled (using direct LLM fallback): {}", e.getMessage());
                this.embeddingModel = null;
            }
        });
        initThread.setName("rag-onnx-init");
        initThread.setDaemon(true);
        initThread.start();
    }

    private void loadStore() {
        try {
            Path path = Paths.get(storageDir, "vector_store.json");
            File file = path.toFile();
            if (file.exists()) {
                this.embeddingStore = InMemoryEmbeddingStore.fromFile(path);
                logger.info("Loaded vector store from {}", path);
            }
        } catch (Exception e) {
            logger.warn("Could not load vector store, starting fresh: {}", e.getMessage());
        }
    }

    private void saveStore() {
        try {
            Path path = Paths.get(storageDir, "vector_store.json");
            ((InMemoryEmbeddingStore<TextSegment>) embeddingStore).serializeToFile(path);
        } catch (Exception e) {
            logger.error("Failed to save vector store", e);
        }
    }

    @Async("ragTaskExecutor")
    public void ingestNote(String noteId) {
        ingestNoteSync(noteId);
    }

    public synchronized void ingestNoteSync(String noteId) {
        if (embeddingModel == null || embeddingStore == null) {
            logger.debug("RAG vector indexing skipped for note {} - embedding model or store not available", noteId);
            return;
        }

        database.getNoteById(noteId).ifPresent(note -> {
            String text = note.getExtractedText();
            if (text == null || text.trim().isEmpty()) return;

            logger.info("Starting RAG ingestion for note: {}", note.getTitle());

            Document document = Document.from(text, Metadata.from("noteId", noteId));
            DocumentSplitter splitter = DocumentSplitters.recursive(400, 50);
            List<TextSegment> segments = splitter.split(document);

            int successCount = 0;
            int failedCount = 0;

            for (TextSegment segment : segments) {
                try {
                    Embedding embedding = embeddingModel.embed(segment).content();
                    embeddingStore.add(embedding, segment);
                    successCount++;
                } catch (Exception e) {
                    logger.error("Failed to embed segment for note {} (segment {}/{})", noteId, successCount + failedCount + 1, segments.size(), e);
                    failedCount++;
                }
            }

            saveStore();
            logger.info("Completed RAG ingestion for note {}. Success: {}, Failed: {}", noteId, successCount, failedCount);
        });
    }

    public String askChapter(String question, String noteId) {
        return askChapter(question, noteId, null);
    }

    public String askChapter(String question, String noteId, String customApiKey) {
        logger.info("RAG query for noteId {} (customApiKey: {}): {}", noteId, (customApiKey != null ? "provided" : "none"), question);

        Optional<Note> optionalNote = database.getNoteById(noteId);
        if (optionalNote.isEmpty()) {
            return "{\"answer\": \"Requested note or chapter material not found in vault.\", \"confidence\": 0.0}";
        }
        Note note = optionalNote.get();
        String extractedText = note.getExtractedText();

        if (extractedText == null || extractedText.trim().isEmpty()
                || extractedText.startsWith("Text extraction only")
                || extractedText.equals("Failed to extract text.")) {
            return "{\"answer\": \"Text extraction is not available for this document (e.g. image-only or scanned PDF). Please refer to the document directly.\", \"confidence\": 0.0}";
        }

        List<TextSegment> filteredSegments = null;
        double topScore = 0.85;

        // Try ONNX embedding search if model is available and initialized
        if (embeddingModel != null && embeddingStore != null) {
            try {
                Embedding questionEmbedding = embeddingModel.embed(question).content();
                List<EmbeddingMatch<TextSegment>> matches = embeddingStore.findRelevant(questionEmbedding, 20);

                boolean hasEmbeddings = matches.stream()
                        .anyMatch(m -> noteId.equals(m.embedded().metadata().getString("noteId")));

                if (!hasEmbeddings) {
                    logger.info("NoteId {} not indexed in vector store. Ingesting synchronously...", noteId);
                    ingestNoteSync(noteId);
                    matches = embeddingStore.findRelevant(questionEmbedding, 20);
                }

                List<EmbeddingMatch<TextSegment>> noteMatches = matches.stream()
                        .filter(m -> noteId.equals(m.embedded().metadata().getString("noteId")))
                        .limit(5)
                        .collect(Collectors.toList());

                if (!noteMatches.isEmpty()) {
                    topScore = noteMatches.get(0).score();
                    filteredSegments = noteMatches.stream()
                            .filter(m -> m.score() > 0.25)
                            .limit(4)
                            .map(EmbeddingMatch::embedded)
                            .collect(Collectors.toList());
                }
            } catch (Exception e) {
                logger.warn("ONNX vector retrieval error: {}. Falling back to direct context extraction.", e.getMessage());
            }
        }

        // Build context from vector segments if available, or extract intelligent context from the document
        String context;
        if (filteredSegments != null && !filteredSegments.isEmpty()) {
            StringBuilder sb = new StringBuilder();
            for (TextSegment seg : filteredSegments) {
                sb.append(seg.text()).append("\n\n");
            }
            context = sb.toString().trim();
        } else {
            context = extractRelevantContext(extractedText, question, 12000);
        }

        String noteTitle = (note.getTitle() != null && !note.getTitle().isBlank()) ? note.getTitle() : "Course Document";
        String systemInstruction = "You are an expert academic AI tutor for EduVault. Answer the student's question accurately and thoroughly based strictly on the provided chapter notes context from \"" + noteTitle + "\". Provide a structured, insightful explanation using markdown formatting (clear headings, bullet points, bold key terms). Return a valid JSON object: {\"answer\": \"markdown formatted answer here\", \"confidence\": 0.95}. Do not include markdown code block tags like ```json around the response.";
        String prompt = "=== CHAPTER NOTE: " + noteTitle + " ===\n"
                + "Context:\n" + context + "\n\n"
                + "Question: " + question + "\n\n"
                + "Return JSON format: {\"answer\": \"...\", \"confidence\": " + String.format(java.util.Locale.US, "%.2f", Math.max(0.75, topScore)) + "}";

        try {
            String response = geminiService.chat(systemInstruction, prompt, 0.2, customApiKey);
            if (response != null && !response.trim().isEmpty()) {
                String cleaned = cleanJson(response);
                if (cleaned.startsWith("{") && cleaned.contains("\"answer\"")) {
                    return cleaned;
                } else if (!cleaned.isBlank()) {
                    Map<String, Object> jsonMap = Map.of(
                            "answer", cleaned,
                            "confidence", Math.max(0.75, topScore)
                    );
                    return mapper.writeValueAsString(jsonMap);
                }
            }
        } catch (Exception e) {
            logger.warn("Gemini RAG inference failed: {}. Falling back to extracted context snippet.", e.getMessage());
        }

        // Direct context fallback if Gemini API call failed
        String fallbackAnswer = "### Relevant Excerpt from " + noteTitle + "\n\n"
                + (context.length() > 2500 ? context.substring(0, 2500) + "\n\n...*(additional document sections available)*" : context);
        try {
            return mapper.writeValueAsString(Map.of(
                    "answer", fallbackAnswer,
                    "confidence", 0.65
            ));
        } catch (Exception ex) {
            return "{\"answer\": \"Could not generate an answer at this time.\", \"confidence\": 0.0}";
        }
    }

    private String cleanJson(String responseText) {
        if (responseText == null) return "{}";
        String text = responseText.trim();
        if (text.startsWith("```json")) {
            text = text.substring(7);
        } else if (text.startsWith("```")) {
            text = text.substring(3);
        }
        if (text.endsWith("```")) {
            text = text.substring(0, text.length() - 3);
        }
        return text.trim();
    }

    private String extractRelevantContext(String fullText, String question, int maxChars) {
        if (fullText == null || fullText.isBlank()) {
            return "";
        }
        if (fullText.length() <= maxChars) {
            return fullText;
        }

        // Split text into paragraphs or blocks
        String[] paragraphs = fullText.split("\\r?\\n\\s*\\r?\\n");
        if (paragraphs.length <= 1) {
            paragraphs = fullText.split("(?<=\\.\\s)");
        }
        if (paragraphs.length <= 1) {
            return fullText.substring(0, maxChars);
        }

        // Tokenize question into keywords
        Set<String> keywords = Arrays.stream(question.toLowerCase().split("\\W+"))
                .filter(w -> w.length() > 2)
                .filter(w -> !STOP_WORDS.contains(w))
                .collect(Collectors.toSet());

        if (keywords.isEmpty()) {
            return fullText.substring(0, maxChars);
        }

        class ScoredParagraph {
            final String text;
            final int score;
            final int index;
            ScoredParagraph(String text, int score, int index) {
                this.text = text;
                this.score = score;
                this.index = index;
            }
        }

        List<ScoredParagraph> scored = new ArrayList<>();
        for (int i = 0; i < paragraphs.length; i++) {
            String p = paragraphs[i].trim();
            if (p.isEmpty()) continue;
            String lower = p.toLowerCase();
            int score = 0;
            for (String kw : keywords) {
                if (lower.contains(kw)) {
                    score += 1;
                }
            }
            scored.add(new ScoredParagraph(p, score, i));
        }

        scored.sort((a, b) -> Integer.compare(b.score, a.score));

        List<ScoredParagraph> selected = new ArrayList<>();
        int currentLength = 0;
        for (ScoredParagraph sp : scored) {
            if (sp.score > 0 || selected.isEmpty()) {
                if (currentLength + sp.text.length() <= maxChars) {
                    selected.add(sp);
                    currentLength += sp.text.length();
                }
            }
            if (currentLength >= maxChars) break;
        }

        selected.sort(Comparator.comparingInt(a -> a.index));
        StringBuilder sb = new StringBuilder();
        for (ScoredParagraph sp : selected) {
            sb.append(sp.text).append("\n\n");
        }
        return sb.toString().trim();
    }
}
