const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

class AICommands {
    constructor(bot) {
        this.bot = bot;
    }

    register() {
        // Chat command
        const chatCommand = {
            data: new SlashCommandBuilder()
                .setName('chat')
                .setDescription('Chat with AI')
                .addStringOption(option =>
                    option.setName('message')
                        .setDescription('Your message to the AI')
                        .setRequired(true)),
            async execute(interaction) {
                await interaction.deferReply();

                try {
                    const message = interaction.options.getString('message');
                    
                    const response = await interaction.client.openai.chat.completions.create({
                        model: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                        messages: [
                            {
                                role: "system",
                                content: "You are a helpful Discord bot assistant. Be friendly, concise, and helpful. Keep responses under 2000 characters."
                            },
                            {
                                role: "user",
                                content: message
                            }
                        ],
                        max_tokens: 500
                    });

                    const aiResponse = response.choices[0].message.content;

                    const embed = new EmbedBuilder()
                        .setTitle('🤖 AI Response')
                        .setDescription(aiResponse)
                        .setColor('#3498db')
                        .setFooter({ text: `Requested by ${interaction.user.username}`, iconURL: interaction.user.displayAvatarURL({ dynamic: true }) })
                        .setTimestamp();

                    await interaction.editReply({ embeds: [embed] });

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'chat', true, `AI chat: ${message.substring(0, 100)}`);

                } catch (error) {
                    console.error('Error in AI chat:', error);
                    await interaction.editReply('Sorry, I encountered an error while processing your request. Please try again later.');
                    
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'chat', false, error.message);
                }
            }
        };

        // Image analysis command
        const analyzeCommand = {
            data: new SlashCommandBuilder()
                .setName('analyze')
                .setDescription('Analyze an image with AI')
                .addAttachmentOption(option =>
                    option.setName('image')
                        .setDescription('Image to analyze')
                        .setRequired(true)),
            async execute(interaction) {
                await interaction.deferReply();

                try {
                    const attachment = interaction.options.getAttachment('image');
                    
                    if (!attachment.contentType || !attachment.contentType.startsWith('image/')) {
                        await interaction.editReply('Please provide a valid image file.');
                        return;
                    }

                    // Download and convert image to base64
                    const response = await fetch(attachment.url);
                    const buffer = await response.arrayBuffer();
                    const base64 = Buffer.from(buffer).toString('base64');

                    const aiResponse = await interaction.client.openai.chat.completions.create({
                        model: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                        messages: [
                            {
                                role: "user",
                                content: [
                                    {
                                        type: "text",
                                        text: "Analyze this image and describe what you see in detail. Include objects, people, activities, colors, and any other notable aspects."
                                    },
                                    {
                                        type: "image_url",
                                        image_url: {
                                            url: `data:${attachment.contentType};base64,${base64}`
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens: 500
                    });

                    const analysis = aiResponse.choices[0].message.content;

                    const embed = new EmbedBuilder()
                        .setTitle('🔍 Image Analysis')
                        .setDescription(analysis)
                        .setColor('#9b59b6')
                        .setImage(attachment.url)
                        .setFooter({ text: `Analyzed by ${interaction.user.username}`, iconURL: interaction.user.displayAvatarURL({ dynamic: true }) })
                        .setTimestamp();

                    await interaction.editReply({ embeds: [embed] });

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'analyze', true, 'Image analysis completed');

                } catch (error) {
                    console.error('Error in image analysis:', error);
                    await interaction.editReply('Sorry, I encountered an error while analyzing the image. Please try again later.');
                    
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'analyze', false, error.message);
                }
            }
        };

        // Summarize command
        const summarizeCommand = {
            data: new SlashCommandBuilder()
                .setName('summarize')
                .setDescription('Summarize text with AI')
                .addStringOption(option =>
                    option.setName('text')
                        .setDescription('Text to summarize')
                        .setRequired(true)),
            async execute(interaction) {
                await interaction.deferReply();

                try {
                    const text = interaction.options.getString('text');
                    
                    if (text.length > 4000) {
                        await interaction.editReply('Text is too long. Please provide text under 4000 characters.');
                        return;
                    }

                    const response = await interaction.client.openai.chat.completions.create({
                        model: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                        messages: [
                            {
                                role: "system",
                                content: "Summarize the following text concisely while maintaining key points and important information. Provide a clear, structured summary."
                            },
                            {
                                role: "user",
                                content: text
                            }
                        ],
                        max_tokens: 300
                    });

                    const summary = response.choices[0].message.content;

                    const embed = new EmbedBuilder()
                        .setTitle('📝 Text Summary')
                        .addFields(
                            { name: 'Original Length', value: `${text.length} characters`, inline: true },
                            { name: 'Summary Length', value: `${summary.length} characters`, inline: true },
                            { name: 'Summary', value: summary, inline: false }
                        )
                        .setColor('#e67e22')
                        .setFooter({ text: `Summarized for ${interaction.user.username}`, iconURL: interaction.user.displayAvatarURL({ dynamic: true }) })
                        .setTimestamp();

                    await interaction.editReply({ embeds: [embed] });

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'summarize', true, `Summarized ${text.length} characters`);

                } catch (error) {
                    console.error('Error in text summarization:', error);
                    await interaction.editReply('Sorry, I encountered an error while summarizing the text. Please try again later.');
                    
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'summarize', false, error.message);
                }
            }
        };

        // Generate command
        const generateCommand = {
            data: new SlashCommandBuilder()
                .setName('generate')
                .setDescription('Generate an image with AI')
                .addStringOption(option =>
                    option.setName('prompt')
                        .setDescription('Description of the image to generate')
                        .setRequired(true)),
            async execute(interaction) {
                await interaction.deferReply();

                try {
                    const prompt = interaction.options.getString('prompt');
                    
                    const response = await interaction.client.openai.images.generate({
                        model: "dall-e-3",
                        prompt: prompt,
                        n: 1,
                        size: "1024x1024",
                        quality: "standard"
                    });

                    const imageUrl = response.data[0].url;

                    const embed = new EmbedBuilder()
                        .setTitle('🎨 Generated Image')
                        .setDescription(`**Prompt:** ${prompt}`)
                        .setColor('#f1c40f')
                        .setImage(imageUrl)
                        .setFooter({ text: `Generated for ${interaction.user.username}`, iconURL: interaction.user.displayAvatarURL({ dynamic: true }) })
                        .setTimestamp();

                    await interaction.editReply({ embeds: [embed] });

                    // Award tokens for using AI features
                    interaction.client.db.addTokens(interaction.guildId, interaction.user.id, 5);

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'generate', true, `Generated image: ${prompt.substring(0, 100)}`);

                } catch (error) {
                    console.error('Error in image generation:', error);
                    await interaction.editReply('Sorry, I encountered an error while generating the image. Please try again later.');
                    
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'generate', false, error.message);
                }
            }
        };

        // Register all commands
        this.bot.commands.set('chat', chatCommand);
        this.bot.commands.set('analyze', analyzeCommand);
        this.bot.commands.set('summarize', summarizeCommand);
        this.bot.commands.set('generate', generateCommand);
    }
}

module.exports = AICommands;