# BlurHash64: Adjustable-Fidelity Glyph Encodings for Proof, Resemblance, Transport, and Non-Executable File Disclosure

## Abstract

This paper proposes BlurHash64, an adjustable-fidelity encoding framework for representing digital files across a continuum from vague, non-executable descriptions to exact, executable byte transport. Conventional cryptographic hashes provide compact irreversible commitments to file identity, while Base64 provides reversible text-safe transport of full binary content. Between these extremes lies an underdeveloped design space: representations that partially resemble, describe, prove, classify, or authorize a file without fully revealing or reconstructing it. BlurHash64 formalizes this middle region as a fidelity ladder. At low fidelity, a glyph may only indicate the existence, type, or broad structure of a file. At intermediate fidelity, it may carry metadata, semantic features, perceptual fingerprints, provenance receipts, or partial redacted fragments. At maximum fidelity, it may carry the complete file body through reversible encoding such as Base64. The framework introduces the notions of projection fidelity, execution threshold, receipt binding, lambda friction, and zero-copy transferability. Its goal is to support controlled disclosure of digital artifacts: a file may stay anchored at one canonical location while transferable glyphs circulate as proofs, sketches, rights, or transport envelopes. The paper argues that BlurHash64 can serve as a foundation for AI production ledgers, digital evidence packets, secure artifact review, privacy-preserving verification, and financeable software receipts.

## 1. Introduction

Digital systems usually treat file representation as a binary choice: either disclose the file or disclose a hash. This is too coarse. A full file disclosure reveals the complete byte sequence and may allow execution, copying, leakage, or unauthorized reuse. A cryptographic hash, by contrast, is compact and useful for integrity verification, but it does not reveal enough about the file to support human evaluation, semantic comparison, economic appraisal, or controlled preview.

This paper proposes a third path: adjustable-fidelity glyph encoding. A glyph is a compact representational object that may contain identity, resemblance, proof, location, access rights, or transport material. A glyph is not necessarily a file. It becomes file-like only when it contains enough recoverable information and is interpreted by a suitable decoder or runtime. The core insight is that file representation can be staged. A low-fidelity glyph may say only that a file exists. A higher-fidelity glyph may say the file is a Python application, a PDF report, an image, or a signed build artifact. A still higher-fidelity glyph may carry feature summaries, perceptual fingerprints, dependency graphs, redacted fragments, provenance receipts, or encrypted payloads. At the highest level, the glyph may contain the complete Base64 body of the file and therefore become reconstructable.

BlurHash64 is not a replacement for cryptographic hashing. Instead, it combines irreversible commitments with reversible or semi-reversible projections. The result is a layered representation in which identity, resemblance, proof, and transport are separated. This separation makes it possible to disclose enough information for a specific purpose without automatically disclosing enough information to execute or fully reconstruct the file.

The motivating use case is the AI-native desktop. Modern work increasingly produces artifacts through a mixture of human action, AI agents, local files, Git repositories, prompts, terminal commands, browser sessions, screenshots, local model outputs, and build systems. These artifacts often need to be reviewed, sold, audited, financed, or transferred without exposing the entire local machine. BlurHash64 provides a language for producing controlled proof objects from such artifacts.

## 2. Background

Cryptographic hash functions produce fixed-length digests from arbitrary input. Secure hash standards such as SHA-256 are designed so that the digest can detect whether a message has changed, but the digest is not intended to reconstruct the original message [1]. This makes a hash an identity commitment rather than a transport format.

Base64 occupies the opposite role. Base64 is a text-safe representation of binary data. It is reversible: if the Base64 string contains the full encoded body and is decoded correctly, the original bytes can be reconstructed [2]. Base64 is therefore not a proof by itself. It is a transport encoding.

Fuzzy hashing and perceptual hashing show that not all hash-like objects need to behave like cryptographic hashes. Context-triggered piecewise hashing was developed to identify files that are similar rather than byte-identical [3]. Perceptual hashing methods similarly aim to produce fingerprints that correlate with perceptual similarity, especially in media contexts such as images and video [4]. These systems demonstrate that hash-like representations can preserve resemblance rather than strict identity.

Merkle trees provide another relevant primitive: many pieces of evidence can be hashed individually and then aggregated into a single root commitment [5]. This is useful when a system wants to commit to many shards while later revealing only selected branches. Zero-knowledge proofs extend this idea of selective disclosure by allowing a prover to demonstrate the truth of a statement without revealing all underlying information [6].

Information theory supplies the limit conditions. Shannon's theory frames communication as the reproduction of messages exactly or approximately under constraints [7]. Kolmogorov complexity frames the shortest effective description of an object as a measure of its underlying structure or compressibility [8]. Together, these ideas clarify why a small glyph cannot reconstruct an arbitrary high-entropy file unless the missing information is stored elsewhere, supplied by a key, or generated by a compact rule.

## 3. Problem Statement

The central problem is controlled file disclosure.

Given a file, different parties may need different levels of knowledge about it. A buyer may need to know that a software artifact exists, was produced at a certain time, passed tests, and does not contain obvious secrets. A reviewer may need a dependency graph or architecture sketch. An auditor may need hash commitments and provenance. A runtime may need the full byte body. A public webpage may need only a safe preview.

Existing primitives do not fully solve this problem. A cryptographic hash is safe but too opaque. Base64 is portable but too revealing if it contains the full body. Encryption protects the body but still moves the complete file material. Perceptual and fuzzy hashes provide resemblance but are domain-specific and may be vulnerable to manipulation. Receipts and signatures provide accountability but do not define a general fidelity ladder.

BlurHash64 addresses this by introducing controlled intermediate representations between pure hash and full body transport.

## 4. Core Concept

BlurHash64 represents a file through a fidelity-indexed projection. Let the original file be treated as a canonical source object. A projection function extracts a representation of the file at fidelity level k. Low k produces vague or non-executable information. High k produces precise or reconstructable information.

At the lowest level, the projection may only indicate existence. At a metadata level, it may include file size, type, timestamp, extension, or media class. At a semantic level, it may include imports, page count, detected entities, dependency structure, visual layout, color histogram, or topic summary. At a proof level, it may include a cryptographic digest, provenance receipt, time anchor, location anchor, and verification claims. At a partial-body level, it may include selected chunks. At an encrypted-body level, it may include the full body but require a key. At a Base64-body level, it carries the exact reconstructable bytes.

The framework separates four properties that are often confused:

Identity: whether the representation can verify sameness.

Resemblance: whether the representation preserves meaningful features.

Recoverability: whether the original can be reconstructed.

Executability: whether the reconstructed object can be executed by a runtime.

A low-fidelity glyph may have resemblance but not recoverability. A hash may have identity but neither resemblance nor recoverability. A Base64 body has recoverability but no inherent proof unless it is also hash-bound and receipt-bound.

## 5. Fidelity Ladder

BlurHash64 defines a ladder of disclosure levels.

Level 0 is the null glyph. It discloses no useful file information.

Level 1 is the presence glyph. It asserts that a file exists, but does not disclose its type or content.

Level 2 is the type glyph. It reveals a broad class such as source code, PDF, image, archive, binary, dataset, or model file.

Level 3 is the metadata glyph. It reveals non-content properties such as size, extension, creation time, modification time, or MIME type.

Level 4 is the feature glyph. It reveals extracted structure such as imports, functions, dependency graph, page count, dominant colors, entity list, schema shape, or media fingerprint.

Level 5 is the sketch glyph. It contains lossy summaries, approximate layouts, semantic descriptions, or partial previews that help humans or machines understand the file without reconstructing it.

Level 6 is the receipt glyph. It contains hash commitments, provenance, location anchors, time anchors, signatures, verification results, and transferability scores. It proves claims about the file without necessarily revealing the body.

Level 7 is the partial-body glyph. It includes selected bytes, chunks, snippets, or redacted fragments. It can reconstruct part of the file, but not the whole.

Level 8 is the encrypted-body glyph. It includes the full body, but access requires a decryption key or external authorization.

Level 9 is the full transport glyph. It includes the complete byte body in a reversible transport format such as Base64. At this level, the glyph can regenerate the original file if correctly decoded.

The boundary between Level 8 and Level 9 is crucial. Both may carry the full file body, but Level 8 is controlled by cryptographic access while Level 9 is directly reconstructable by anyone who can decode it.

## 6. Execution Threshold

BlurHash64 introduces an execution threshold. A glyph becomes executable only when it contains enough byte-level information, access material, and runtime context to produce an executable object.

A low-fidelity glyph cannot execute because it does not contain a byte-complete program. A metadata glyph cannot execute because it only describes. A receipt glyph cannot execute because it proves claims but does not contain the program body. A partial-body glyph may execute only if the missing parts are supplied elsewhere. An encrypted-body glyph may execute only after decryption. A Base64-body glyph may execute if decoded into a valid executable format and passed to a compatible runtime.

Therefore, execution is not a property of Base64 alone. Execution requires body sufficiency, decoding, file boundary reconstruction, permissions, and runtime interpretation.

## 7. Lambda Friction and Transferability

A central contribution of BlurHash64 is lambda friction. Lambda measures the difficulty of transferring, verifying, reconstructing, or using a glyph outside its original environment.

A glyph has high lambda if it depends on local paths, hidden credentials, undocumented runtime assumptions, proprietary hardware, missing build scripts, private context, or unavailable witnesses. A glyph has low lambda if it can be verified, interpreted, reconstructed, or authorized with minimal external dependency.

Transferability is inversely related to lambda. A cryptographic hash may have low storage cost but high interpretive friction if no one knows what file it refers to. A Base64 body may have high recoverability but high disclosure risk. A receipt-bound glyph can reduce lambda by attaching location, time, provenance, signature, and verification claims.

This gives BlurHash64 an economic role: it can rank artifacts not only by what they are, but by how easily they can become useful to another party.

## 8. Zero-Copy Transfer

BlurHash64 supports zero-copy transfer. In this model, the original file remains at one canonical location. The file is not copied. Instead, glyphs circulate as proofs, previews, rights, access tokens, or transport envelopes.

A stationary file may emit many glyphs. One glyph may be a public proof of existence. Another may be a buyer preview. Another may be an auditor receipt. Another may be an encrypted inspection package. Another may be a full Base64 body for authorized reconstruction.

This separates file mobility from proof mobility. The file may stay still while its verification surface travels.

## 9. Security and Privacy Considerations

BlurHash64 does not make disclosure safe automatically. Each fidelity level carries risk.

Low-fidelity glyphs may leak existence. Metadata glyphs may leak sensitive timing, size, or format information. Feature glyphs may leak semantic content. Perceptual glyphs may allow similarity inference. Receipt glyphs may reveal provenance or workflow details. Partial-body glyphs may leak confidential fragments. Encrypted-body glyphs depend on key management. Full Base64 glyphs are complete disclosures.

The system must therefore include explicit disclosure policies. A glyph should declare its fidelity level, reconstructability, execution potential, proof claims, and redaction status. A verifier should distinguish between cryptographic integrity, semantic resemblance, and executable completeness.

The paper also recommends crypto-agility. If receipts are intended to survive long time horizons, signature schemes should be designed so that they can migrate as cryptographic standards evolve. Recent post-quantum standards make this especially relevant for long-lived evidence systems [9].

## 10. Proposed Architecture

A practical BlurHash64 system has five modules.

The first module is the projector. It extracts fidelity-controlled representations from files.

The second module is the commitment engine. It hashes the original file, projections, chunks, and receipts.

The third module is the receipt engine. It binds hashes to provenance, time, location, verification claims, signatures, and lambda scores.

The fourth module is the encoder. It serializes glyphs into transport-safe forms such as text, QR, URL-safe payloads, JSON, PDF attachments, or Base64 envelopes.

The fifth module is the verifier. It checks whether a glyph proves identity, provides resemblance, enables recovery, or crosses the execution threshold.

In AI production systems, the architecture can be extended with screen events, file deltas, Git commits, terminal commands, build results, tests, and artifact exports. These events can be sharded, hashed, and aggregated into receipt roots.

## 11. Evaluation Plan

BlurHash64 should be evaluated across six dimensions.

The first is fidelity accuracy: whether each level discloses the intended amount of information.

The second is non-executability: whether low and intermediate levels reliably avoid reconstructing executable files.

The third is resemblance utility: whether feature and sketch glyphs help humans or machines classify, compare, or price artifacts.

The fourth is proof strength: whether receipt glyphs correctly verify identity, time, location, and provenance claims.

The fifth is privacy leakage: whether lower-fidelity glyphs accidentally reveal more than intended.

The sixth is transferability: whether lambda scores predict the practical effort required for a third party to verify, inspect, rebuild, or use the artifact.

A benchmark suite should include code repositories, PDFs, images, datasets, app bundles, archives, and AI-generated artifacts. Each file should be represented at multiple fidelity levels and tested for reconstruction risk, semantic utility, verification correctness, and downstream usability.

## 12. Applications

BlurHash64 has immediate applications in AI-assisted software development. A developer can send a low-fidelity glyph to prove that an artifact exists, a receipt glyph to prove tests passed, a feature glyph to describe architecture, and a full transport glyph only after payment or authorization.

In digital forensics, BlurHash64 could support staged disclosure where investigators, auditors, and legal reviewers receive only the level of detail they are authorized to inspect.

In data rooms and software acquisition, BlurHash64 can support financeable artifact packets. A seller can prove that an app, dataset, or report exists and is structured in a particular way without immediately disclosing the full asset.

In privacy-preserving AI workflows, BlurHash64 can support local-first systems where source files remain stationary while proof objects circulate.

In compliance, BlurHash64 can provide receipts that demonstrate control evidence, build provenance, or absence-of-secret checks without disclosing confidential source material.

## 13. Limitations

BlurHash64 is not a magic compression system. A small glyph cannot reconstruct an arbitrary high-entropy file unless the missing information exists in a generator, key, location, witness, or external store. This follows from information-theoretic limits.

BlurHash64 is also not a substitute for formal cryptographic proof. A receipt is only as strong as its verifier, hash function, signature scheme, and evidence capture process. A semantic sketch may be useful, but it is not equivalent to file identity. A perceptual hash may indicate similarity, but it does not provide the same guarantee as a cryptographic hash.

The system must also avoid misleading notation. A glyph that looks mathematically strong but lacks a verifier should be treated as symbolic, not cryptographic.

## 14. Conclusion

BlurHash64 proposes an adjustable-fidelity model for digital file representation. It separates identity, resemblance, recoverability, executability, proof, and transferability. In doing so, it fills the space between opaque cryptographic hashes and fully revealing Base64 bodies.

The main contribution is a controlled disclosure ladder. At low fidelity, a glyph vaguely describes or proves existence. At intermediate fidelity, it resembles, classifies, sketches, or verifies. At high fidelity, it carries enough material to reconstruct or execute. The model is especially useful for AI-native workflows where artifacts must be audited, transferred, sold, financed, or verified without indiscriminate copying.

The core principle is simple: not every representation of a file should be the file. Some representations should prove, some should resemble, some should authorize, and only some should transport the full body. BlurHash64 gives these modes a common notation and architecture.

## References

[1] NIST FIPS 180-4 defines secure hash algorithms as digests used to detect whether messages have changed.

[2] RFC 4648 defines Base16, Base32, and Base64 encodings.

[3] Kornblum's 2006 work introduced context-triggered piecewise hashing for identifying almost identical files.

[4] Perceptual image hashing is a known family of approaches for similarity-oriented file fingerprints.

[5] Merkle's work underlies hash-tree commitments for aggregating many hashed leaves into a compact root.

[6] Goldwasser, Micali, and Rackoff introduced zero-knowledge proof systems, where correctness can be proven without revealing additional knowledge.

[7] Shannon's information theory frames exact or approximate message reproduction and entropy limits.

[8] Kolmogorov complexity formalizes the shortest effective description of an object, which explains why arbitrary files cannot be losslessly represented by tiny glyphs unless they are highly compressible or externally witnessed.

[9] NIST finalized the first three post-quantum cryptography standards in 2024, which is relevant for long-lived signed receipts.
