extern "C"{
	void registerExtensionClasses();

	int  AKUCreateSceneContext();
	void AKUReleaseSceneContext( int id );
	void AKUUpdateSceneContext( int id, double step );
	void AKURenderSceneContext( int id );

}
