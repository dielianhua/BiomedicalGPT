# Source corpora, licences and references

All 20 source corpora of this dataset, with their task type, accession URL, licence and the
corresponding entry in the manuscript's reference list. Each training record also carries a `source_url` field; this table is the single
authority for those URLs.

`Train` and `Test` are the number of items contributed to `data/train/v1_DS_27k.json` (27,673) and
`data/test/test_4800.json` (4,800) respectively.

| Source dataset   | Task     | Train      | Test      | Accession URL                                           | Licence                                                  | Ref. |
| ---------------- | -------- | ----------:| ---------:| ------------------------------------------------------- | -------------------------------------------------------- | ----:|
| MedQA            | QA       | 10,178     | 1,273     | https://github.com/jind11/MedQA                         | MIT                                                      | 24   |
| NCBI-disease     | NER      | 5,432      | 100       | https://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/ | Research use under provider terms                        | 12   |
| BC5CDR           | NER      | 4,560      | 100       | https://github.com/JHnlp/BioCreative-V-CDR-Corpus       | Research use under provider terms                        | 13   |
| MedDialog        | TXTCLASS | 981        | 122       | https://github.com/UCSD-AI4H/Medical-Dialogue-System    | Research use under provider terms                        | 26   |
| SciFact          | TE       | 868        | 319       | https://github.com/allenai/scifact                      | CC BY 4.0 (claims/evidence); ODC-By 1.0 (abstracts)      | 25   |
| BioNLP-2011-GE   | NER      | 856        | 100       | https://2011.bionlp-st.org/                             | No formal licence; open participation (shared-task data) | 16   |
| BioNLP-2009      | NER      | 756        | 260       | https://www.nactem.ac.uk/GENIA/SharedTask/              | No formal licence; open participation (shared-task data) | 15   |
| BioNLP-2011-REL  | NER      | 756        | 260       | https://2011.bionlp-st.org/                             | No formal licence; open participation (shared-task data) | 18   |
| BioInfer-RE      | RE       | 642        | 142       | https://github.com/metalrt/ppi-dataset                  | Research use under provider terms                        | 27   |
| BC5CDR-RE        | RE       | 500        | 500       | https://github.com/JHnlp/BioCreative-V-CDR-Corpus       | Research use under provider terms                        | 13   |
| PubMedQA-labeled | QA       | 450        | 500       | https://pubmedqa.github.io/                             | MIT                                                      | 23   |
| BioRED           | NER      | 400        | 100       | https://ftp.ncbi.nlm.nih.gov/pub/lu/BioRED/             | Research use under provider terms                        | 22   |
| BioNLP-2013-CG   | NER      | 300        | 200       | https://2013.bionlp-st.org/                             | No formal licence; open participation (shared-task data) | 19   |
| MLEE-COREF       | COREF    | 198        | 113       | https://www.nactem.ac.uk/MLEE/                          | CC BY-NC-SA 3.0                                          | 28   |
| BioNLP-2013-GE   | NER      | 194        | 256       | https://2013.bionlp-st.org/                             | No formal licence; open participation (shared-task data) | 20   |
| AnEM             | NER      | 164        | 137       | https://www.nactem.ac.uk/anatomy/                       | Creative Commons BY-SA 3.0                               | 14   |
| BioNLP-2011-ID   | NER      | 151        | 117       | https://2011.bionlp-st.org/                             | No formal licence; open participation (shared-task data) | 17   |
| BioNLP-2013-GRO  | NER      | 150        | 100       | https://2013.bionlp-st.org/                             | No formal licence; open participation (shared-task data) | 21   |
| MLEE-EE          | EE       | 127        | 87        | https://www.nactem.ac.uk/MLEE/                          | CC BY-NC-SA 3.0                                          | 28   |
| AnEM-COREF       | COREF    | 10         | 14        | https://www.nactem.ac.uk/anatomy/                       | Creative Commons BY-SA 3.0                               | 14   |
| **Total**        |          | **27,673** | **4,800** |                                                         |                                                          |      |

# 

## References

Numbering follows the manuscript's reference list; only the entries that back the table above are
reproduced here.

12. Doğan, R. I., Leaman, R., & Lu, Z. (2014). NCBI disease corpus: A resource for disease name
    recognition and concept normalization. *Journal of Biomedical Informatics*, 47, 1–10.
    https://doi.org/10.1016/j.jbi.2013.12.006
13. Li, J., Sun, Y., Johnson, R. J., Sciaky, D., Wei, C.-H., Leaman, R., Davis, A. P., Mattingly, C. J.,
    Wiegers, T. C., & Lu, Z. (2016). BioCreative V CDR task corpus: a resource for chemical disease
    relation extraction. *Database: The Journal of Biological Databases and Curation*, 2016, baw068.
    https://doi.org/10.1093/database/baw068
14. Ohta, T., Pyysalo, S., Tsujii, J., & Ananiadou, S. (2012). Open-domain anatomical entity mention
    detection. In *Proceedings of the Workshop on Detecting Structure in Scholarly Discourse*
    (pp. 27–36). Association for Computational Linguistics, Jeju Island, Korea.
15. Kim, J.-D., Ohta, T., Pyysalo, S., Kano, Y., & Tsujii, J. (2009). Overview of BioNLP'09 Shared Task
    on Event Extraction. In *Proceedings of the BioNLP 2009 Workshop Companion Volume for Shared Task*
    (pp. 1–9). Association for Computational Linguistics, Boulder, Colorado.
16. Kim, J.-D., Nguyen, N., Wang, Y., Tsujii, J., Takagi, T., & Yonezawa, A. (2012). The Genia Event and
    Protein Coreference tasks of the BioNLP Shared Task 2011. *BMC Bioinformatics*, 13(Suppl 11), S1.
    https://doi.org/10.1186/1471-2105-13-S11-S1
17. Pyysalo, S., Ohta, T., Rak, R., Sullivan, D., Mao, C., Wang, C., Sobral, B., Tsujii, J., &
    Ananiadou, S. (2012). Overview of the ID, EPI and REL tasks of BioNLP Shared Task 2011.
    *BMC Bioinformatics*, 13(Suppl 11), S2. https://doi.org/10.1186/1471-2105-13-S11-S2
18. Pyysalo, S., Ohta, T., & Tsujii, J. (2011). Overview of the Entity Relations (REL) Supporting Task
    of BioNLP Shared Task 2011. In *Proceedings of BioNLP Shared Task 2011 Workshop* (pp. 83–88).
    Association for Computational Linguistics, Portland, Oregon, USA.
19. Pyysalo, S., Ohta, T., & Ananiadou, S. (2013). Overview of the Cancer Genetics (CG) task of BioNLP
    Shared Task 2013. In *Proceedings of the BioNLP Shared Task 2013 Workshop* (pp. 58–66).
    Association for Computational Linguistics, Sofia, Bulgaria.
20. Kim, J.-D., Wang, Y., & Yasunori, Y. (2013). The Genia Event Extraction Shared Task, 2013 Edition –
    Overview. In *Proceedings of the BioNLP Shared Task 2013 Workshop* (pp. 8–15). Association for
    Computational Linguistics, Sofia, Bulgaria.
21. Kim, J.-J., Han, X., Lee, V., & Rebholz-Schuhmann, D. (2013). GRO Task: Populating the Gene
    Regulation Ontology with events and relations. In *Proceedings of the BioNLP Shared Task 2013
    Workshop* (pp. 50–57). Association for Computational Linguistics, Sofia, Bulgaria.
22. Luo, L., Lai, P.-T., Wei, C.-H., Arighi, C. N., & Lu, Z. (2022). BioRED: a rich biomedical relation
    extraction dataset. *Briefings in Bioinformatics*, 23(5), bbac282.
    https://doi.org/10.1093/bib/bbac282
23. Jin, Q., Dhingra, B., Liu, Z., Cohen, W., & Lu, X. (2019). PubMedQA: A Dataset for Biomedical
    Research Question Answering. In *Proceedings of EMNLP-IJCNLP 2019* (pp. 2567–2577). Association for
    Computational Linguistics, Hong Kong, China. https://doi.org/10.18653/v1/D19-1259
24. Jin, D., Pan, E., Oufattole, N., Weng, W.-H., Fang, H., & Szolovits, P. (2021). What Disease Does
    This Patient Have? A Large-Scale Open Domain Question Answering Dataset from Medical Exams.
    *Applied Sciences*, 11(14), 6421. https://doi.org/10.3390/app11146421
25. Wadden, D., Lin, S., Lo, K., Wang, L. L., van Zuylen, M., Cohan, A., & Hajishirzi, H. (2020).
    Fact or Fiction: Verifying Scientific Claims. In *Proceedings of EMNLP 2020* (pp. 7534–7550).
    Association for Computational Linguistics, Online. https://doi.org/10.18653/v1/2020.emnlp-main.609
26. Zeng, G., Yang, W., Ju, Z., Yang, Y., Wang, S., Zhang, R., Zhou, M., Zeng, J., Dong, X., Zhang, R.,
    Fang, H., Zhu, P., Chen, S., & Xie, P. (2020). MedDialog: Large-scale Medical Dialogue Datasets.
    In *Proceedings of EMNLP 2020* (pp. 9241–9250). Association for Computational Linguistics, Online.
    https://doi.org/10.18653/v1/2020.emnlp-main.743
27. Pyysalo, S., Ginter, F., Heimonen, J., Björne, J., Boberg, J., Järvinen, J., & Salakoski, T. (2007).
    BioInfer: a corpus for information extraction in the biomedical domain. *BMC Bioinformatics*, 8, 50.
    https://doi.org/10.1186/1471-2105-8-50
28. Pyysalo, S., Ohta, T., Miwa, M., Cho, H.-C., Tsujii, J., & Ananiadou, S. (2012). Event extraction
    across multiple levels of biological organization. *Bioinformatics*, 28(18), i575–i581.
    https://doi.org/10.1093/bioinformatics/bts407
