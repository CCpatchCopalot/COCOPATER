We created six ablated versions for CoCoPATER (See [RQ2 results](https://github.com/CCpatchCopalot/COCOPATER/tree/main/RQ2.Ablation/results.json))

    (1) identifying critical functions using the LLM without the intra-/inter-procedural signatures extraction module (w/o Sig);

    (2) removing the critical function chains construction module (w/o FC); 

    (3) switching GPT-4o to GPT-3.5 [39] (w/GPT3.5);

    (4) removing the equivalent transformation module (w/o trans);

    (5) identifying critical statements using the LLM without the core statement sequence extraction module (w/o Seq);

    (6) removing the monitor module (w/o mon);

To get the results of the ablated versions, follow the similiar step of RQ1.